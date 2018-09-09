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
                logging.debug('swap at base: %d', base)
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
        the half inning backwards from when the swap happened."""
        inning_to_search = self.flat_atbats[swap_idx].inning
        for atbat in reversed(self.flat_atbats[:swap_idx]):
            for runner in atbat.runners:
                if runner.id == original_runner_id:
                    assert runner.end
                    return runner.end
            if atbat.inning != inning_to_search:
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
        """Adds a scoring string to each atbat as well as applying various
        'fixes' to the runners."""
        outs = 0
        active_runners = []
        for atbat in half_inning:
            atbat.scoring = get_scoring(atbat)
            self.fix_mid_pa_runners(atbat)
            if atbat.outs != 3:
                self.resolve_runners_easy(atbat, atbat.outs - outs)
            else:
                continue
            #self.fix_runners(atbat.outs - outs, atbat)
            self.hold_runners(active_runners, atbat)

            active_runners = [r for r in atbat.runners
                              if not r.out and r.end != 4]
            outs = atbat.outs
            self.display_atbat(atbat)
            #input()

    def resolve_runners_easy(self, atbat, outs_on_play):
        """Easy aka outs !=3...if no batter runner, batter is out, but check
        also for a single/double/triple and out on bases."""
        outs_on_play -= sum([1 for r in atbat.mid_pa_runners if r.out])
        batter_runner = [r for r in atbat.runners if r.id == atbat.batter]
        runners_to_adjust = [r for r in atbat.runners if not r.end]
        runner_outs = len(runners_to_adjust)

        batter_out = 1 if not batter_runner else 0
        if outs_on_play != runner_outs + batter_out:
            # Walkoff, runner on base that doesn't score
            if self.flat_atbats[-1] == atbat:
                return
            else:
                raise Exception()

        for runner in runners_to_adjust:
            runner.end = self.find_base_where_out_was_made(
                self.players[runner.id].last, atbat.des)
            runner.out = True
            logging.debug('Runner end adjusted: %s %d',
                          self.players[runner.id], runner.end)

        if not batter_runner and atbat.event in ['Single', 'Double', 'Triple']:
            base = self.find_base_where_out_was_made(
                self.players[atbat.batter].last, atbat.des)
            atbat.add_runner(
                Runner(atbat.batter, 0, base, atbat.event_num, True))
            logging.warning('Runner inserted: batter is out at %d' % base)

    def display_atbat(self, atbat):
        logging.debug('%d %s (%s)', atbat.pa_num, atbat.scoring.code,
                      atbat.scoring.result)
        logging.debug(atbat.des)
        self.display_runners(atbat.mid_pa_runners)
        if atbat.mid_pa_runners:
            logging.debug('-----mid_pa above-----------')
        self.display_runners(atbat.runners)
        logging.debug('%d out', atbat.outs)

    def display_runners(self, runners):
        for runner in runners:
            insert = ''
            if runner.out:
                insert = ' (out)'
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

    def is_batter_out(self, atbat):
        """Tries to determine if the batter is out on the play. This is not
        always accurate, most notably on double plays and inning ending plays
        where the batter is safe."""
        batter_runner = [r for r in atbat.runners if r.id == atbat.batter]

        # 1. Simplest case, not the end of an inning, no batter runner
        if not batter_runner and atbat.outs != 3:
            if atbat.scoring.result != 'out':
                logging.warning('Scoring result is not out, but batter out?')
            if (atbat.event in ('Single', 'Double', 'Triple')):
                atbat.add_runner(Runner(atbat.batter, 0, 0, atbat.event_num))
                return False
            return True

        # 2. Read description to see if batter out mentioned
        if re.search('%s out at' % self.players[atbat.batter].last, atbat.des):
            if (atbat.event in ('Single', 'Double', 'Triple')):
                atbat.add_runner(Runner(atbat.batter, 0, 0, atbat.event_num))
                return False
            return True

        # End of inning, batter safe won't show up as a runner tag
        # Previous case should catch a batter out if the scoring is 'on-base'
        if (not batter_runner and atbat.outs == 3 and
                atbat.scoring.result == 'on-base'):
            return False

        if (not batter_runner and
                not re.match('With .* batting,', atbat.des) and
                not len(re.findall('out at', atbat.des)) > 1):
            # Triple play with the batter safe would error here ;-)
            return True
        else:
            return False

    def get_outs_to_resolve(self, atbat, outs_to_resolve):
        """Returns the number of outs recorded on a play excluding runners
        thrown out during the plate appearance and the batter if he is out."""
        outs_to_resolve -= sum([1 for r in atbat.mid_pa_runners if r.out])
        if self.is_batter_out(atbat):
            outs_to_resolve -= 1
        #logging.warning('Batter is out %s', self.is_batter_out(atbat))
        logging.warning('Outs to resolve: %d', outs_to_resolve)
        return outs_to_resolve

    def fix_runners(self, outs_on_play, atbat):
        """All runners should have both a start and end attribute. However the
        API uses end="" to signify both the runner being put out as well as
        runners stranded on base to end an inning. This examines all runners
        without an ending base and attempts to record either an out or hold
        runners who were stranded. Runners put out have their ending base
        recorded based on examination of the atbat's description."""
        runners_to_adjust = [r for r in atbat.runners if not r.end]
        if not runners_to_adjust:
            return

        outs_to_resolve = self.get_outs_to_resolve(atbat, outs_on_play)
        if outs_to_resolve:
            runners_to_adjust = [r for r in atbat.runners if not r.end]
            for runner in runners_to_adjust:
                try:
                    runner.end = self.find_base_where_out_was_made(
                        self.players[runner.id].last, atbat.des)
                    runner.out = True
                    logging.debug('Runner end adjusted: %s %d',
                                  self.players[runner.id], runner.end)
                except Exception:
                    pass

            runners_out = [r for r in runners_to_adjust if r.out]
            if len(runners_out) < outs_to_resolve:
                logging.error(atbat.__dict__)
                raise Exception('Not all marked out that should be')
            elif len(runners_out) != outs_to_resolve:
                logging.error(atbat.__dict__)
                raise Exception('Over resolved')

            # (if outs !=3 no one can be stranded)
            if (len(runners_to_adjust) != len(runners_out) and
                    atbat.outs != 3):
                raise Exception('Runner should not be stranded')

        # Stranded runners
        for runner in atbat.runners:
            if not runner.end:
                runner.end = runner.start

    def find_base_where_out_was_made(self, runner_last_name, des):
        """Given the last name of a runner and a description of the play, this
        returns the base where that runner was put out."""
        logging.debug('Last name: %s', runner_last_name)
        logging.debug('Description: %s', des)
        g = re.search(('%s %s %s' %
                       (runner_last_name, OUTS_ON_BASES, LONG_BASE)), des)
        if g:
            return BASE_NUMBER[g.group(1)]

        g = re.search(PICKS_OFF + ' %s at %s' % (runner_last_name, LONG_BASE),
                      des)
        if g:
            return BASE_NUMBER[g.group(1)]

        raise Exception('Cannot find base where %s was put out:\n%s' %
                        (runner_last_name, des))
