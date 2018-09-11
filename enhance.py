import re
from copy import deepcopy
import logging

from fuzzywuzzy import fuzz

from scoring import get_scoring
from models import Runner

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
    def __init__(self, game, players):
        self.innings = game.innings
        self.flat_atbats = sum([i.top + i.bottom for i in self.innings], [])
        self.actions = game.actions
        self.players = players

        self.fix_pinch_runners()

        for inning in self.innings:
            self.fix_inning(inning)

    def fix_pinch_runners(self):
        """When a pinch runner is inserted into the game, in addition to the
        action tag, sometimes the 'swap' is further noted by a pair of runner
        tags. EX: <runner start="2B" end=""/> <runner start="" end="2B"/>
        These unhelpful tags need to be removed so they are not confused with
        actual runner movement or outs on the bases."""
        for action in self.actions.values():
            if self.is_pinch_runner(action):
                pinch_id, original_id = self.get_pinch_runner_swap(action)
                logging.debug('%d replaces %d', pinch_id, original_id)
                index = self.get_atbat_index(action.event_num)
                base = self.get_runner_last_base(index, original_id)
                logging.debug('Swap at base: %d', base)
                self.remove_pinch_runner_swap(
                    self.flat_atbats[index].runners,
                    pinch_id, original_id, base)
                self.remove_pinch_runner_swap(
                    self.flat_atbats[index].mid_pa_runners,
                    pinch_id, original_id, base)

    def is_pinch_runner(self, action):
        return (action.event == 'Offensive Sub' and
                'Offensive Substitution: Pinch-runner' in action.des)

    def get_pinch_runner_swap(self, action):
        """Inspects the action description and returns the ids of the pinch
        runner and the runner he is replacing."""
        g = re.search('Pinch-runner (.*) replaces (.*).', action.des)
        pinch_runner_name = g.group(1).strip()
        original_runner_name = g.group(2).strip()
        logging.debug('%s replaces %s', pinch_runner_name,
                      original_runner_name)

        pinch_runner_id = self.lookup_player(pinch_runner_name)
        original_runner_id = self.lookup_player(original_runner_name)
        return pinch_runner_id, original_runner_id

    def lookup_player(self, full_name):
        """Tries to lookup a player record given the full name."""
        for player in self.players.values():
            if player.full_name() == full_name:
                return player.id
        for player in self.players.values():  # Second try!
            if fuzz.ratio(player.full_name(), full_name) > 80:
                return player.id
        raise Exception('Player %s not found' % full_name)

    def get_atbat_index(self, event_num):
        for i, atbat in enumerate(self.flat_atbats):
            if atbat.event_num > event_num:
                return i

    def get_runner_last_base(self, swap_idx, original_runner_id):
        """Returns the base where the pinch runner swap occurs by searching
        the half inning backwards from when the swap happened. First, check for
        runner advancement during the PA beofre when pinch runner appeared."""
        mid_pa_advances = [r for r in self.flat_atbats[swap_idx].mid_pa_runners
                          if r.id == original_runner_id]
        if mid_pa_advances:
            return max([r.end for r in mid_pa_advances])

        for atbat in reversed(self.flat_atbats[:swap_idx]):
            for runner in atbat.runners:
                if runner.id == original_runner_id:
                    assert runner.end
                    return runner.end
            if atbat.inning != self.flat_atbats[swap_idx].inning:
                break
        raise Exception('Base not found')

    def remove_pinch_runner_swap(
            self, runners, pinch_runner_id, original_runner_id, base):
        p_r, o_r = -1, -1
        for i, runner in enumerate(runners):
            logging.debug('%d, %s', i, runner)
            if (runner.id == pinch_runner_id and
                    runner.start == 0 and runner.end == base):
                p_r = i
            elif (runner.id == original_runner_id and
                  runner.start == base and runner.end == 0):
                o_r = i
        logging.debug('p_r: %d, o_r: %d', p_r, o_r)
        if p_r >= 0 and o_r >= 0:
            logging.debug('Deleting runners from pinch swap')
            for i in sorted([p_r, o_r], reverse=True):
                del runners[i]
        else:
            logging.debug('No runner swap')

    def fix_inning(self, inning):
        self.fix_half_inning(inning.top)
        self.fix_half_inning(inning.bottom)

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
            input()

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
            logging.warning('Runner inserted: batter is out at %d' % base)

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
            logging.warning('Runner inserted: batter is out at %d',
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
                logging.warning('Runner inserted: batter to %d', base)
            elif not batter_out_base and atbat.event != 'Runner Out':
                atbat.add_runner(Runner(atbat.batter, 0, 1, atbat.event_num))
                logging.warning('Runner inserted: batter to 1st')

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
        """When all runners simply hold on a play, there are no runner tags.
        This creates Runner instances to record holding on a base."""
        if not atbat.runners and active_runners:
            atbat.runners = deepcopy(active_runners)
            for runner in atbat.runners:
                logging.debug('Held Runner: %s', self.players[runner.id])
                runner.start = runner.end
                runner.event_num = atbat.event_num

    def fix_mid_pa_runners(self, atbat):
        """All runner tags in the middle of the plate appearance without an
        ending base are out on the basepaths. This records the base and marks
        the runner out. This is typically a caught stealing or pickoff."""
        for runner in atbat.mid_pa_runners:
            if not runner.end:
                runner.end = self.find_base_where_out_was_made(
                    self.players[runner.id].last,
                    self.actions[runner.event_num].des)
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
