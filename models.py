from collections import namedtuple

Action = namedtuple('Action', 'event_num event des player')


class Runner:
    def __init__(self, id, start, end, event_num, out=False):
        self.id = id
        self.start = start
        self.end = end
        self.event_num = event_num
        self.out = out
        self.to_score = False

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class Game:
    def __init__(self):
        self.innings = []

    def add_inning(self, inning):
        self.innings.append(inning)


class Inning:
    def __init__(self, num):
        self.num = int(num)
        self.halves = []

    def add_half(self, half_inning):
        if not self.halves:
            half_inning.num = self.num
        else:
            half_inning.num = self.num + 0.5
        self.halves.append(half_inning)
        assert len(self.halves) in (1, 2)

    def __str__(self):
        return 'Inning %d' % (self.num)


class HalfInning:
    def __init__(self):
        self.atbats = []
        self.init_action_buffer()

    def init_action_buffer(self):
        self.action_buffer = []

    def add_atbat(self, atbat):
        for action in self.action_buffer:
            atbat.add_action(action)
        self.atbats.append(atbat)
        self.init_action_buffer()

    def add_action(self, action):
        self.action_buffer.append(action)


class AtBat:
    def __init__(self, pa_num, event_num, batter, des, event, pitcher,
                 outs=0, home_score=0, away_score=0,
                 mid_pa_runners=None, runners=None, scoring=None):

        self.pa_num = pa_num
        self.event_num = event_num
        self.batter = batter
        self.des = des
        self.event = event
        self.pitcher = pitcher

        self.outs = outs

        if mid_pa_runners:
            self.mid_pa_runners = mid_pa_runners
        else:
            self.mid_pa_runners = list()

        if runners:
            self.runners = runners
        else:
            self.runners = list()

        self.home_score = home_score
        self.away_score = away_score

        self.scoring = scoring
        self.actions = []

    def get_action_by_event_num(self, event_num):
        for action in self.actions:
            if action.event_num == event_num:
                return action
        raise KeyError

    def add_runner(self, runner):
        if runner.event_num < self.event_num:
            self.mid_pa_runners.append(runner)
        elif runner.event_num == self.event_num:
            self.runners.append(runner)
        else:
            raise Exception('Runner bad ordering')

    def add_action(self, action):
        self.actions.append(action)

    def get_description(self):
        descriptions = [a.des for a in self.actions]
        if self.des not in descriptions:
            descriptions.append(self.des)
        return '\n'.join(descriptions)
