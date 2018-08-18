import re
import xml.etree.ElementTree as ET
from copy import deepcopy

from state import AtBat, Runner

BASES = ('1B', '2B', '3B')


class GameParser:
    def __init__(self, xml, players):
        self.event_types = set()

        self.inning = 1.0
        self.events = []
        self.active_atbat = None
        self.players = players
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
        self.events.append(self.active_atbat)

    def parse_atbat(self, atbat):
        pa_num = int(atbat.attrib['num'])
        event_num = int(atbat.attrib['event_num'])
        batter = int(atbat.attrib['batter'])
        des = re.sub('\s\s+', ' ', atbat.attrib['des'].strip())
        event = atbat.attrib['event']
        outs = int(atbat.attrib['o'])
        home_score = int(atbat.attrib['home_team_runs'])
        away_score = int(atbat.attrib['away_team_runs'])

        if batter not in self.players:
            raise Exception('id not found %d' % batter)

        self.active_atbat = AtBat(pa_num, event_num, batter, des, event,
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

        print(self.active_atbat.__dict__)

    def parse_action(self, action):
        print('  - %s (%s) %s' % (action.tag, action.attrib['event_num'],
                                  action.attrib['des']))

    def parse_runner(self, runner):
        id = int(runner.attrib['id'])
        if id not in self.players:
            raise Exception('id not found %d' % id)
        start, end = self.get_runner_start_end(runner)
        event_num = int(runner.attrib['event_num'])
        self.active_atbat.runners.append(Runner(id, start, end, event_num))

    def get_runner_start_end(self, runner):
        start = self.parse_base(runner.attrib['start'])
        end = self.parse_base(runner.attrib['end'])
        # '' is either runner scoring or end of inning, runner stranded
        if end == 0:
            if runner.attrib.get('score') == 'T':
                end = 4
            elif self.active_atbat.outs == 3:
                end = start
        return start, end

    def parse_base(self, base):
        if not base:
            return 0
        elif base in BASES:
            return int(base[0])
        else:
            raise Exception('Could not parse base: %s' % base)

    def get_player_str(self, id):
        p = self.players[id]
        return '%d %s. %s' % (p.id, p.first[0], p.last)


if __name__ == '__main__':
    with open('inning_all.xml') as f:
        g = GameParser(f.read())
    print('All Event Types: ' + str(g.event_types))
    print(len(g.events))
