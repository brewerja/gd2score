from collections import namedtuple
import re
import logging

from .scoring import get_scoring

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
        retval = '       ' + ' '.join([str(x) for x in [self.id, self.start,
                                                       '->', self.end]])
        if self.out:
            retval += ' out!'
        elif self.to_score and self.end == 4:
            retval += ' scores!'
        elif self.to_score:
            retval += ' will score'
        return retval
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class Iter:
    def __init__(self, array):
        self.array = array

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(self.array):
            ret_val = self.array[self._n]
            self._n += 1
            return ret_val
        else:
            raise StopIteration


class Game(Iter):
    def __init__(self):
        self.in_progress = False
        self.innings = []
        Iter.__init__(self, self.innings)

    def add_inning(self, inning):
        self.innings.append(inning)


class Inning(Iter):
    def __init__(self, num):
        self.num = int(num)
        self.halves = []
        Iter.__init__(self, self.halves)

    def add_half(self, half_inning):
        if not self.halves:
            half_inning.num = self.num
        else:
            half_inning.num = self.num + 0.5
        self.halves.append(half_inning)
        assert len(self.halves) in (1, 2)

    def __str__(self):
        return 'Inning %d' % (self.num)


class HalfInning(Iter):
    def __init__(self):
        self.atbats = []
        self.init_action_buffer()
        Iter.__init__(self, self.atbats)

    def init_action_buffer(self):
        self.action_buffer = []

    def add_atbat(self, atbat):
        for action in self.action_buffer:
            atbat.add_action(action)
        self.atbats.append(atbat)
        self.init_action_buffer()

    def add_action(self, action):
        self.action_buffer.append(action)

    def __str__(self):
        if self.num % 1.0:
            return '  Bottom %d' % (self.num)
        return '  Top %d' % (self.num)

class AtBat:
    def __init__(self, pa_num, event_num, batter, des, event, pitcher,
                 outs=0, home_score=0, away_score=0,
                 mid_pa_runners=None, runners=None):

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

        self.actions = []
        self.scoring = get_scoring(self)

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

    def __str__(self):
        retval = '    ' + ' '.join(
            [str(x) for x in [self.pa_num, self.batter, self.pitcher,
                              self.outs, self.scoring.code]])
        if self.scoring.result == 'on-base':
            retval += ' ' + self.event
        elif self.scoring.result == 'error':
            retval += ' (error)'
        return retval


class Player:
    def __init__(self, id, first, last):
        self.id = id
        if re.match('[A-Z]\.\s?[A-Z]\.\s*', first):
            # 'A.J.' --> 'A. J.'
            self.first = '%s %s' % (first[:2], first[2:])
        else:
            self.first = first
        self.last = last

    def full_name(self):
        return ' '.join((self.first, self.last))

    def __str__(self):
        uppers = ['%s.' % c for c in self.first if c.isupper()]
        return '%s %s' % (' '.join(uppers), self.last)

    def __repr__(self):
        return self.__str__()
