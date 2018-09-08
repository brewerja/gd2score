import re
import xml.etree.ElementTree as ET

from models import AtBat, Runner, Inning, Action

BASES = ('1B', '2B', '3B')


class GameParser:
    def __init__(self, game_xml):
        self.inning = 1.0
        self.active_inning = None
        self.active_atbat = None

        self.innings = []
        self.actions = {}

        self.parse_game(game_xml)

    def parse_game(self, xml):
        for inning in ET.fromstring(xml):
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

        for event in half_inning:
            self.parse_event(event)

    def parse_event(self, event):
        if event.tag == 'atbat':
            self.parse_atbat(event)
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

        self.active_inning.add_event(self.active_atbat)

        for child in atbat:
            if child.tag == 'runner':
                self.parse_runner(child)
            elif child.tag in ['pitch', 'po']:
                pass
            else:
                raise Exception('Unknown atbat type: %s' % child.tag)

    def parse_action(self, action):
        event_num = int(action.attrib['event_num'])
        event = action.attrib['event']
        des = re.sub('\s+', ' ', action.attrib['des']).strip()
        player_id = int(action.attrib['player'])
        a = Action(event_num, event, des, player_id)
        self.add_action(a)

    def parse_runner(self, runner):
        id = int(runner.attrib['id'])
        start = self.parse_base(runner.attrib['start'])
        end = self.parse_base(runner.attrib['end'])
        event_num = int(runner.attrib['event_num'])

        if runner.attrib.get('score') == 'T':  # Scores!
            end = 4
        self.active_atbat.add_runner(Runner(id, start, end, event_num))

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
