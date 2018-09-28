import re
import logging
from itertools import chain

from scoring import get_scoring
from models import Runner
from parse_players import Player
from runner_highlighter import RunnerHighlighter

BASE_NUMBER = {
    '1st': 1,
    '2nd': 2,
    '3rd': 3,
    'home': 4
}

OUTS_ON_BASES = ('(?:out at|doubled off|picked off and caught stealing|'
                 'caught stealing|was picked off)')

LONG_BASE = '(%s)' % '|'.join(BASE_NUMBER.keys())

PICKS_OFF = 'picks off .*'

HITS_IN_PARK = ('Single', 'Double', 'Triple')


class GameEnhancer:
    def __init__(self):
        self.runner_highlighter = RunnerHighlighter()

    def execute(self, game):
        self.game = game
        self.players = game.players
        self.players[0] = Player(0, 'Held', 'Runner')
        self.enhance()

    def enhance(self):
        for inning in self.game.innings:
            self.fix_half_inning(inning.top)
            self.fix_half_inning(inning.bottom)

        self.highlight_runners_who_score()

    def fix_half_inning(self, half_inning):
        """Adds a scoring string to each atbat, adds missing runner tags, and
        resolves the ending bases of runners with empty end tags."""
        outs = 0
        active_runners = []
        for atbat in half_inning:
            atbat.scoring = get_scoring(atbat)
            self.fix_mid_pa_runners(atbat)

            outs_on_play = (atbat.outs - outs -
                            sum([1 for r in atbat.mid_pa_runners if r.out]))
            if atbat.outs != 3:
                self.resolve_runners_easy(atbat, outs_on_play)
            else:
                self.resolve_runners_3outs(atbat, outs_on_play)

            self.hold_runners(active_runners, atbat)

            active_runners = [r for r in atbat.runners
                              if not r.out and r.end != 4]
            outs = atbat.outs
            self.display_atbat(atbat)

    def resolve_runners_easy(self, atbat, outs_on_play):
        """When there's less than 3 outs, the lack of a runner tag for the
        batter means that the batter is out. Also, all empty end attributes on
        runners mean the runner is out."""
        self.set_runner_out_bases(atbat)

        runner_outs = sum([1 for r in atbat.runners if r.out])
        batter_runner = [r for r in atbat.runners if r.id == atbat.batter]
        batter_out = 1 if not batter_runner else 0

        if outs_on_play != runner_outs + batter_out:
            # Walkoff, runner on base that doesn't score
            if self.flat_atbats[-1] == atbat:
                return
            else:
                raise Exception()

        # Batter out trying to take an extra base
        if not batter_runner and atbat.event in HITS_IN_PARK:
            base = self.find_base_where_out_was_made(
                self.players[atbat.batter].last, atbat.des)
            atbat.add_runner(
                Runner(atbat.batter, 0, base, atbat.event_num, out=True))
            logging.debug('Runner inserted: batter is out at %d' % base)

    def resolve_runners_3outs(self, atbat, outs_on_play):
        """When the inning ends, the absences of a runner tag for the batter
        does not necessarily mean that the batter is out. So the approach is
        different. Look for runner outs in the description first. Not all empty
        end attributes mean an out. Stranded runners are also empty."""
        self.set_runner_out_bases(atbat, throw=False)

        batter_out_base = self.find_base_where_out_was_made(
            self.players[atbat.batter].last, atbat.des, throw=False)

        # Batter out trying to take an extra base
        if batter_out_base and atbat.event in HITS_IN_PARK:
            atbat.add_runner(
                Runner(atbat.batter, 0, batter_out_base, atbat.event_num,
                       out=True))
            logging.debug('Runner inserted: batter is out at %d',
                          batter_out_base)

        runner_outs = sum([1 for r in atbat.runners if r.out])
        if outs_on_play - runner_outs > 0:
            # Batter should be out, so no need for runner tag
            if atbat.scoring.result == 'on-base':
                raise Exception('Batter should be out')
        else:  # Batter not out, need to create stranded runner
            if not batter_out_base and atbat.event in HITS_IN_PARK:
                base = HITS_IN_PARK.index(atbat.event) + 1
                atbat.add_runner(
                    Runner(atbat.batter, 0, base, atbat.event_num))
                logging.debug('Runner inserted: batter to %d', base)
            elif not batter_out_base and atbat.event != 'Runner Out':
                atbat.add_runner(Runner(atbat.batter, 0, 1, atbat.event_num))
                logging.debug('Runner inserted: batter to 1st')

        self.strand_remaining_runners(atbat)

    def set_runner_out_bases(self, atbat, throw=True):
        runners_to_adjust = [r for r in atbat.runners if not r.end]
        for runner in runners_to_adjust:
            try:
                runner.end = self.find_base_where_out_was_made(
                    self.players[runner.id].last, atbat.des)
                runner.out = True
                logging.debug('Runner end adjusted: %s out at %d',
                              self.players[runner.id], runner.end)
            except Exception as e:
                if throw:
                    raise e

    def strand_remaining_runners(self, atbat):
        for runner in atbat.runners:
            if not runner.end and not runner.out:
                runner.end = runner.start

    def display_atbat(self, atbat):
        logging.debug('%d %s (%s)', atbat.pa_num, atbat.scoring.code,
                      atbat.scoring.result)
        logging.debug(atbat.des)
        self.display_runners(atbat.mid_pa_runners)
        if atbat.mid_pa_runners:
            logging.debug('-----mid_pa runners above-----')
        self.display_runners(atbat.runners)
        logging.debug('%d out', atbat.outs)

    def display_runners(self, runners):
        for runner in runners:
            insert = ''
            if runner.out:
                insert = ' (out)'
            elif not runner.out and runner.end == 4:
                insert = ' (scores)'
            logging.debug('%s: %d -> %d%s', self.players[runner.id],
                          runner.start, runner.end, insert)

    def hold_runners(self, active_runners, atbat):
        """The schema only represents runner movement. We need a record in each
        atbat even when the runners hold. This algorithm doesn't worry about
        who the runners are (pinch runners gum up the system) and so it creates
        dummy runners."""
        occupied_bases = [r.end for r in active_runners]
        assert len(occupied_bases) == len(set(occupied_bases))

        for runner in atbat.mid_pa_runners:
            assert runner.start in occupied_bases
            occupied_bases.remove(runner.start)
            if not runner.out and runner.end != 4:
                occupied_bases.append(runner.end)
        assert len(occupied_bases) == len(set(occupied_bases))

        starting_bases = set([r.start for r in atbat.runners])
        for base in set(occupied_bases).difference(starting_bases):
            atbat.add_runner(Runner(0, base, base, atbat.event_num))

    def get_mid_pa_end_base(self, atbat, runner_id):
        return max([r.end for r in atbat.mid_pa_runners if r.id == runner_id])

    def get_runner_end_base_previous_pa(self, atbat, runner_id):
        atbat_idx = self.get_atbat_index(atbat.event_num)
        prev_atbat = self.flat_atbats[atbat_idx - 1]
        return [r for r in prev_atbat.runners if r.id == runner_id][0].end

    def fix_mid_pa_runners(self, atbat):
        """All runner tags in the middle of the plate appearance without an
        ending base are out on the basepaths. This records the base and marks
        the runner out. This is typically a caught stealing or pickoff."""
        for runner in atbat.mid_pa_runners:
            if not runner.end:
                runner.end = self.find_base_where_out_was_made(
                    self.players[runner.id].last,
                    self.game.actions[runner.event_num].des)
                runner.out = True

    def find_base_where_out_was_made(self, runner_last_name, des, throw=True):
        """Given the last name of a runner and a description of the play, this
        returns the base where that runner was put out."""
        g = re.search(('%s %s %s' %
                       (runner_last_name, OUTS_ON_BASES, LONG_BASE)), des)
        if g:
            return BASE_NUMBER[g.group(1)]

        g = re.search(PICKS_OFF + ' %s at %s' % (runner_last_name, LONG_BASE),
                      des)
        if g:
            return BASE_NUMBER[g.group(1)]

        if throw:
            raise Exception('Cannot find base where %s was put out:\n%s' %
                            (runner_last_name, des))

    def highlight_runners_who_score(self):
        half_innings = chain.from_iterable(
            ((i.top, i.bottom) for i in self.game.innings))

        for half_inning in half_innings:
            self.runner_highlighter.highlight(half_inning)
