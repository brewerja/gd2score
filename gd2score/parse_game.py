import re
import xml.etree.ElementTree as ET

from .models import Game, Inning, HalfInning, Action, AtBat, Runner

BASES = ('1B', '2B', '3B')


class GameParser:
    def parse(self, xml):
        game = Game()
        for inning in ET.fromstring(xml):
            game.add_inning(self.parse_inning(inning))
        return game

    def parse_inning(self, inning):
        active_inning = Inning(float(inning.attrib['num']))
        for half_inning in inning:
            active_inning.add_half(self.parse_half_inning(half_inning))
        return active_inning

    def parse_half_inning(self, half_inning):
        if len(half_inning) == 0:
            raise IncompleteGameException()

        half = HalfInning()
        for event in half_inning:
            if event.tag == 'atbat':
                half.add_atbat(self.parse_atbat(event))
            elif event.tag == 'action':
                half.add_action(self.parse_action(event))
            else:
                raise Exception('Unknown event type')
        return half

    def parse_atbat(self, atbat):
        pa_num = int(atbat.attrib['num'])
        event_num = int(atbat.attrib['event_num'])
        batter = int(atbat.attrib['batter'])
        des = re.sub('\s\s+', ' ', atbat.attrib['des'].strip())
        event = atbat.attrib['event']
        outs = int(atbat.attrib['o'])
        home_score = int(atbat.attrib['home_team_runs'])
        away_score = int(atbat.attrib['away_team_runs'])
        pitcher = int(atbat.attrib['pitcher'])

        active_atbat = AtBat(pa_num, event_num, batter, des, event,
                             pitcher, outs,
                             home_score=home_score, away_score=away_score)

        for child in atbat:
            if child.tag == 'runner':
                active_atbat.add_runner(self.parse_runner(child))
            elif child.tag in ['pitch', 'po']:
                pass
            else:
                raise Exception('Unknown atbat type: %s' % child.tag)

        return active_atbat

    def parse_action(self, action):
        event_num = int(action.attrib['event_num'])
        event = action.attrib['event']
        des = re.sub('\s+', ' ', action.attrib['des']).strip()
        player_id = int(action.attrib['player'])
        return Action(event_num, event, des, player_id)

    def parse_runner(self, runner):
        id = int(runner.attrib['id'])
        start = self.parse_base(runner.attrib['start'])
        end = self.parse_base(runner.attrib['end'])
        event_num = int(runner.attrib['event_num'])

        if runner.attrib.get('score') == 'T':  # Scores!
            end = 4
        return Runner(id, start, end, event_num)

    def parse_base(self, base):
        if not base:
            return 0
        elif base in BASES:
            return int(base[0])
        else:
            raise Exception('Could not parse base: %s' % base)


class IncompleteGameException(Exception):
    pass
