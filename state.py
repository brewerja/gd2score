from collections import namedtuple

Runner = namedtuple('Runner', 'id start end event_num')

class AtBat:
    def __init__(self, pa_num, event_num, batter, des, event,
                 inning=1.0, outs=0, runners=None,
                 home_score=0, away_score=0):

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


# Think about pinch runners...need to know runner's "slot in the inning"

# Intentional walk says on_2b for eatch pitch?? No runner element
# Pick offs
