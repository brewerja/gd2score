import re
import xml.etree.ElementTree as ET
from copy import deepcopy

from fuzzywuzzy import fuzz

from state import AtBat, Runner, Inning, Action, PinchRunnerSwap
from scoring import get_scoring

BASES = ('1B', '2B', '3B')

BASE_NUMBER = {
    '1st': 1,
    '2nd': 2,
    '3rd': 3,
    'home': 4
}

OUTS_ON_BASES = ('(?:out at|doubled off|picked off and caught stealing|'
                 'caught stealing|was picked off)')

LONG_BASE = '(%s)' % '|'.join(BASE_NUMBER.keys())

PICKS_OFF = 'picks off .*'


class GameParser:
    def __init__(self, game_xml, players):
        self.inning = 1.0
        self.innings = []
        self.active_inning = None
        self.active_atbat = None
        self.actions = {}
        self.players = players
        self.pinch_runner_swap = None

        self.parse_game(game_xml)


    def parse_game(self, xml):
        game = ET.fromstring(xml)

        for inning in game:
            self.parse_inning(inning)

    def parse_inning(self, inning):
        self.inning = float(inning.attrib['num'])
        self.active_inning = Inning(self.inning)
        self.innings.append(self.active_inning)

        for half_inning in inning:
            self.parse_half_inning(half_inning)

    def parse_half_inning(self, half_inning):
        if half_inning.tag == 'bottom':
            self.inning += 0.5
        #print('\nInning: %.1f' % self.inning)

        for event in half_inning:
            self.parse_event(event)

    def parse_event(self, event):
        if event.tag == 'atbat':
            self.parse_atbat(event)
            self.active_inning.add_event(self.active_atbat)
        elif event.tag == 'action':
            self.parse_action(event)
        else:
            raise Exception('Unknown event type')

    def parse_atbat(self, atbat):
        pa_num = int(atbat.attrib['num'])
        event_num = int(atbat.attrib['event_num'])
        batter = int(atbat.attrib['batter'])
        des = re.sub('\s\s+', ' ', atbat.attrib['des'].strip())
        event = atbat.attrib['event']
        outs = int(atbat.attrib['o'])
        home_score = int(atbat.attrib['home_team_runs'])
        away_score = int(atbat.attrib['away_team_runs'])

        self.active_atbat = AtBat(pa_num, event_num, batter, des, event,
                                  self.inning, outs,
                                  home_score=home_score,
                                  away_score=away_score)

        self.active_atbat.scoring = get_scoring(self.active_atbat)

        for child in atbat:
            if child.tag == 'runner':
                self.parse_runner(child)
            elif child.tag in ['pitch', 'po']:
                pass
            else:
                raise Exception('Unknown atbat type: %s' % child.tag)

        if self.pinch_runner_swap:
            self.check_for_and_remove_pinch_runner_swap()

        #print(self.active_atbat.__dict__)
        #print(self.active_atbat.scoring)
        #input()

    def check_for_and_remove_pinch_runner_swap(self):
        base = self.pinch_runner_swap.base
        p_r, o_r = -1, -1
        for i, runner in enumerate(self.active_atbat.runners):
            if (runner.id == self.pinch_runner_swap.sub.id and
                runner.start == 0 and runner.end == base):
                p_r = i
            elif (runner.id == self.pinch_runner_swap.original.id and
                  runner.start == base and runner.end == 0):
                o_r = i
        if p_r >= 0 and o_r >= 0:
            print('DELETING SWAP')
            print(self.active_atbat.__dict__)
            for i in sorted([p_r, o_r], reverse=True):
                del self.active_atbat.runners[i]
            print(self.active_atbat.__dict__)
        else:
            pass  # Swap not shown in runner tags...nothing to remove

        self.pinch_runner_swap = None

    def parse_action(self, action):
        event_num = int(action.attrib['event_num'])
        event = action.attrib['event']
        des = re.sub('\s+', ' ', action.attrib['des']).strip()
        player_id = int(action.attrib['player'])

        a = Action(event_num, event, des, player_id)

        if (event == 'Offensive Sub' and
                'Offensive Substitution: Pinch-runner' in des):
            self.set_pinch_runner_swap(des)

        self.add_action(a)
        #print('%s: (%s) %s\n%s' % (action.tag,
                                   #action.attrib['event_num'],
                                   #action.attrib['event'],
                                   #action.attrib['des']))

    def set_pinch_runner_swap(self, des):
        g = re.search('Pinch-runner (.*) replaces (.*).', des)
        pinch_runner = g.group(1).strip()
        original_runner = g.group(2).strip()
        print(pinch_runner, '-->', original_runner)
        pr_id, or_id = None, None
        for player in self.players.values():  # TODO: Don't use fuzz
            if fuzz.ratio(player.full_name(), pinch_runner) > 80:
                pr_id = player.id
            elif fuzz.ratio(player.full_name(), original_runner) > 80:
                or_id = player.id
        if not pr_id or not or_id:
            raise Exception("Can't find pinch runner swap")

        self.pinch_runner_swap = PinchRunnerSwap(
            self.players[pr_id], self.players[or_id],
            self.get_runner_last_base(or_id))

    def get_runner_last_base(self, id):
        for ab in reversed(self.active_inning.get_current_half(self.inning)):
            for runner in ab.runners:
                if runner.id == id:
                    return runner.end
        raise Exception("Can't find where PR starts")

    def parse_runner(self, runner):
        id = int(runner.attrib['id'])
        start = self.parse_base(runner.attrib['start'])
        end = self.parse_base(runner.attrib['end'])
        event_num = int(runner.attrib['event_num'])
        out = False  # Decide later which to make True

        if runner.attrib.get('score') == 'T':  # Scores!
            end = 4
        self.active_atbat.add_runner(Runner(id, start, end, event_num, out))

    def parse_base(self, base):
        if not base:
            return 0
        elif base in BASES:
            return int(base[0])
        else:
            raise Exception('Could not parse base: %s' % base)

    def find_base_where_out_was_made(self, runner_last_name, des):
        g = re.search(('%s %s %s' %
                       (runner_last_name, OUTS_ON_BASES, LONG_BASE)), des)
        if g:
            return BASE_NUMBER[g.group(1)]

        g = re.search(PICKS_OFF + ' %s at %s' % (runner_last_name, LONG_BASE),
                      des)
        if g:
            return BASE_NUMBER[g.group(1)]

        else:
            print(runner_last_name)
            print(des)
            raise Exception('Cannot figure out base')

    def add_action(self, action):
        if action.event_num not in self.actions:
            self.actions[action.event_num] = action
        else:
            raise Exception('Duplicate action: %d' % action.event_num)
