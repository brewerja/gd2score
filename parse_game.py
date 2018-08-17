import xml.etree.ElementTree as ET
from copy import deepcopy

from state import State

class GameParser:
    def __init__(self, xml):
        self.event_types = set()

        self.inning = 1.0
        self.events = []
        self.active_event = None
        self.parse_game(xml)

    def parse_game(self, xml):
        game = ET.fromstring(xml)

        for inning in game:
            self.parse_inning(inning)

    def parse_inning(self, inning):
        self.inning = float(inning.attrib['num'])

        for half_inning in inning:
            self.parse_half_inning(half_inning)

    def parse_half_inning(self, half_inning):
        if half_inning.tag == 'bottom':
            self.inning += 0.5
        print('\nInning: %.1f' % self.inning)

        for event in half_inning:
            self.parse_event(event)

    def parse_event(self, event):
        self.event_types.add(event.attrib['event'])
        if event.tag == 'atbat':
            self.parse_atbat(event)
        elif event.tag == 'action':
            self.parse_action(event)
        else:
            raise Exception('Unknown event type')
        self.events.append(self.active_event)

    def parse_atbat(self, atbat):
        pa_num = int(atbat.attrib['num'])
        batter = atbat.attrib['batter']
        des = atbat.attrib['des']
        event = atbat.attrib['event']
        outs = atbat.attrib['o']
        home_score = atbat.attrib['home_team_runs']
        away_score = atbat.attrib['away_team_runs']

        self.active_event = State(pa_num, batter, des, event,
                                  self.inning, outs,
                                  home_score=home_score,
                                  away_score=away_score)

        for child in atbat:
            if child.tag == 'runner':
                self.parse_runner(child)
            elif child.tag in ['pitch', 'po']:
                pass
            else:
                raise Exception('Unknown atbat type: %s' % child.tag)

        print(self.active_event.__dict__)

    def parse_action(self, action):
        print('  - %s (%s) %s' % (action.tag, action.attrib['event_num'],
                                  action.attrib['des']))

    def parse_runner(self, runner):
        id = runner.attrib['id']
        end = runner.attrib['end']

        if end == '1B':
            self.active_event.on_1b = id
        elif end == '2B':
            self.active_event.on_2b = id
        elif end == '3B':
            self.active_event.on_3b = id
        elif (end == '' and 'score' in runner.attrib and
              runner.attrib['score'] == 'T'):
            self.active_event.at_hp.append(id)


if __name__ == '__main__':
    with open('inning_all.xml') as f:
        g = GameParser(f.read())
    print('All Event Types: ' + str(g.event_types))
    print(len(g.events))
