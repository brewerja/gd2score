import re
import xml.etree.ElementTree as ET
from copy import deepcopy

from state import AtBat, Runner, Inning, Action
from scoring import get_scoring

BASES = ('1B', '2B', '3B')


class GameParser:
    def __init__(self, xml):
        self.inning = 1.0
        self.innings = []
        self.active_inning = None
        self.active_atbat = None
        self.actions = {}
        self.parse_game(xml)

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

        for child in atbat:
            if child.tag == 'runner':
                self.parse_runner(child)
            elif child.tag in ['pitch', 'po']:
                pass
            else:
                raise Exception('Unknown atbat type: %s' % child.tag)

        print(self.active_atbat.__dict__)
        print(self.active_atbat.scoring)
        #input()

    def parse_action(self, action):
        a = Action(int(action.attrib['event_num']),
                   action.attrib['event'],
                   re.sub('\s+', ' ', action.attrib['des']).strip())

        self.add_action(a)
        print('%s: (%s) %s\n%s' % (action.tag,
                                  action.attrib['event_num'],
                                  action.attrib['event'],
                                  action.attrib['des']))

    def parse_runner(self, runner):
        id = int(runner.attrib['id'])
        start, end = self.get_runner_start_end(runner)
        event_num = int(runner.attrib['event_num'])
        self.active_atbat.add_runner(Runner(id, start, end, event_num))

    def get_runner_start_end(self, runner):
        start = self.parse_base(runner.attrib['start'])
        end = self.parse_base(runner.attrib['end'])
        # '' is either runner scoring, stranded to end inning, or out
        # No runner tags when they don't move, unless stranded to end inning
        event_num = int(runner.attrib['event_num'])
        if end == 0:
            if runner.attrib.get('score') == 'T':  # Scores!
                end = 4
            elif (self.active_atbat.outs == 3 and
                  self.active_atbat.event_num == event_num):  # Stranded
                end = start
            else:
                print('Runner out on the bases')
                # TODO: figure out the base, look for 'X out at (base)'
        return start, end

    def parse_base(self, base):
        if not base:
            return 0
        elif base in BASES:
            return int(base[0])
        else:
            raise Exception('Could not parse base: %s' % base)

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
