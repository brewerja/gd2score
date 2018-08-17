class State:
    def __init__(self, pa_num, batter, des, event,
                 inning=1.0, outs=0,
                 on_1b=None, on_2b=None, on_3b=None, at_hp=None,
                 home_score=0, away_score=0):

        self.pa_num = pa_num
        self.batter = batter
        self.des = des
        self.event = event

        self.inning = inning
        self.outs = outs

        self.on_1b = on_1b
        self.on_2b = on_2b
        self.on_3b = on_3b
        if at_hp:
            self.at_hp = at_hp
        else:
            self.at_hp = list()

        self.home_score = home_score
        self.away_score = away_score


# Think about pinch runners...need to know runner's "slot in the inning"
# Think about runners scoring on the same play...multiples "at home"

# End of inning with stranded runners, end="" for all, no scores
# Runners scoring, also end="" for runners

# Intentional walk says on_2b for eatch pitch?? No runner element
