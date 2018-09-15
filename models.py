from collections import namedtuple

Action = namedtuple('Action', 'event_num event des player')


class Runner:
    def __init__(self, id, start, end, event_num, out=False):
        self.id = id
        self.start = start
        self.end = end
        self.event_num = event_num
        self.out = out

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class Inning:
    def __init__(self, num):
        self.num = int(num)
        self.top = []
        self.bottom = []
        self.actions = {}

    def add_event(self, event):
        if event.inning % 1.0:
            self.bottom.append(event)
        else:
            self.top.append(event)

    def get_current_half(self, inning):
        if inning % 1.0:
            return self.bottom
        else:
            return self.top

    def __str__(self):
        return 'Inning %d: %d %d' % (self.num, len(self.top), len(self.bottom))


class AtBat:
    def __init__(self, pa_num, event_num, batter, des, event,
                 inning=1.0, outs=0, home_score=0, away_score=0,
                 mid_pa_runners=None, runners=None, scoring=None):

        self.pa_num = pa_num
        self.event_num = event_num
        self.batter = batter
        self.des = des
        self.event = event

        self.inning = inning
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
        return '\n'.join([a.des for a in self.actions] + [self.des])
