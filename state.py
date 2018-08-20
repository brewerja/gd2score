from collections import namedtuple

Runner = namedtuple('Runner', 'id start end event_num')


class Inning:
    def __init__(self, num):
        self.num = int(num)
        self.top = []
        self.bottom = []

    def add_event(self, event):
        if event.inning % 1.0:
            self.bottom.append(event)
        else:
            self.top.append(event)

    def __str__(self):
        return 'Inning %d: %d %d' % (self.num, len(self.top), len(self.bottom))


class AtBat:
    def __init__(self, pa_num, event_num, batter, des, event,
                 inning=1.0, outs=0, runners=None,
                 home_score=0, away_score=0, scoring=None):

        self.pa_num = pa_num
        self.event_num = event_num
        self.batter = batter
        self.des = des
        self.event = event

        self.inning = inning
        self.outs = outs

        if runners:
            self.runners = runners
        else:
            self.runners = list()

        self.home_score = home_score
        self.away_score = away_score

        self.scoring = scoring


# Think about pinch runners...need to know runner's "slot in the inning"

# Intentional walk says on_2b for eatch pitch?? No runner element
# Pick offs
