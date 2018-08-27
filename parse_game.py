import re
import xml.etree.ElementTree as ET
from copy import deepcopy

from state import AtBat, Runner, Inning, Action
from scoring import get_scoring

BASES = ('1B', '2B', '3B')

BASE_NUMBER = {
    '1st': 1,
    '2nd': 2,
    '3rd': 3,
    'home': 4
}

OUTS_ON_BASES = ('(?:out at|doubled off|picked off and caught stealing|'
                 'caught stealing)')

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
        self.active_pinch_runner = False
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
        print('\nInning: %.1f' % self.inning)

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

        self.children_ct = len(atbat)
        for i, child in enumerate(atbat):
            self.child_no = i + 1
            if child.tag == 'runner':
                self.parse_runner(child)
            elif child.tag in ['pitch', 'po']:
                pass
            else:
                raise Exception('Unknown atbat type: %s' % child.tag)

        print(self.active_atbat.__dict__)
        print(self.active_atbat.scoring)
        self.active_pinch_runner = False  # Reset in case swap not in runners
        #input()

    def parse_action(self, action):
        event_num = int(action.attrib['event_num'])
        event = action.attrib['event']
        des = re.sub('\s+', ' ', action.attrib['des']).strip()
        player_id = int(action.attrib['player'])

        a = Action(event_num, event, des, player_id)

        if (event == 'Offensive Sub' and
            'Offensive Substitution: Pinch-runner' in des):
            self.active_pinch_runner = True
            self.pinch_runner_ctr = 0

        self.add_action(a)
        print('%s: (%s) %s\n%s' % (action.tag,
                                  action.attrib['event_num'],
                                  action.attrib['event'],
                                  action.attrib['des']))

    def parse_runner(self, runner):
        id = int(runner.attrib['id'])
        start = self.parse_base(runner.attrib['start'])
        end = self.parse_base(runner.attrib['end'])
        event_num = int(runner.attrib['event_num'])
        out = False
        
        if (self.active_pinch_runner and 
                self.active_atbat.event_num == event_num):
            self.pinch_runner_ctr += 1
            if self.pinch_runner_ctr == 2:
                self.active_pinch_runner = False

            # TODO: Multiple PRs would break this, so need to validate PRs
            # If 1st, lookup player name, replaces X in action des
            # If 2nd, lookup player name, replaces X in action des
            print('PR COUNTER %d' % self.pinch_runner_ctr)
            return  # Ignore, this should be a pinch runner swap

        # '' is either runner scoring, stranded to end inning, or out
        # No runner tags when they don't move, unless stranded to end inning
        if end == 0:
            if runner.attrib.get('score') == 'T':  # Scores!
                end = 4
            elif (self.active_atbat.outs == 3 and
                  self.active_atbat.event_num == event_num):  # Stranded
                end = start
                # Or possibly inning ending out on the bases
                if (event_num in self.actions and
                        self.actions[event_num].player == id):
                    out = True
                    runner_last_name = self.players[id].last
                    print('INNING ENDING OUT ON BASES')
                    end = self.find_base_where_out_was_made(
                            runner_last_name, self.active_atbat.des)
            else:  # Out on the bases
                if self.active_atbat.event_num == event_num:
                    out = True
                    runner_last_name = self.players[id].last
                    print('DP/FORCEOUT/FIELDERS CHOICE, ETC.')
                    print(id)
                    end = self.find_base_where_out_was_made(
                            runner_last_name, self.active_atbat.des)
                elif (event_num in self.actions):
                    # and self.actions[event_num].player == id):
                    # Reviews list the team asking for the call
                    out = True
                    runner_last_name = self.players[id].last
                    print('MID AB OUT ON BASES')
                    end = self.find_base_where_out_was_made(
                            runner_last_name, self.actions[event_num].des)
                else:
                    raise Exception('Missing runner out??')

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
            print('HERE HERE HERE')
            return BASE_NUMBER[g.group(1)]

        else:
            print(runner_last_name)
            print(self.active_atbat.des)
            raise Exception('Cannot figure out base')

    def add_action(self, action):
        if action.event_num not in self.actions:
            self.actions[action.event_num] = action
        else:
            raise Exception('Duplicate action: %d' % action.event_num)


if __name__ == '__main__':
    with open('inning_all_1.xml') as f:
        g = GameParser(f.read())
        for event_num in sorted(g.actions.keys()):
            print(g.actions[event_num])
