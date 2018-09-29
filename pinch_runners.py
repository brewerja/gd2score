import logging
import re

from fuzzywuzzy import fuzz


class PinchRunnerFixer:
    def fix(self, atbat, half_inning, players):
        """When a pinch runner is inserted into the game, in addition to the
        action tag, sometimes the 'swap' is further noted by a pair of runner
        tags. EX: <runner start="2B" end=""/> <runner start="" end="2B"/>
        These unhelpful tags need to be removed so they are not confused with
        actual runner movement or outs on the bases."""
        self.players = players
        for action in atbat.actions:
            if self.is_pinch_runner(action):
                pinch_id, original_id = self.get_pinch_runner_swap(action)
                logging.debug('%d replaces %d', pinch_id, original_id)
                base = self.get_swap_base(atbat, half_inning, original_id)
                logging.debug('Swap at base: %d', base)
                self.remove_pinch_runner_swap(
                    atbat.runners, pinch_id, original_id, base)
                self.remove_pinch_runner_swap(
                    atbat.mid_pa_runners, pinch_id, original_id, base)

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

    def get_swap_base(self, atbat, half_inning, original_runner_id):
        """Returns the base where the pinch runner swap occurs by searching
        the half inning backwards from when the swap happened. First, check for
        runner advancement during the PA beofre when pinch runner appeared."""
        mid_pa_advances = [r for r in atbat.mid_pa_runners
                           if r.id == original_runner_id]
        if mid_pa_advances:
            return max([r.end for r in mid_pa_advances])

        swap_idx = half_inning.atbats.index(atbat)
        for atbat in reversed(half_inning.atbats[:swap_idx]):
            for runner in atbat.runners:
                if runner.id == original_runner_id:
                    assert runner.end
                    return runner.end
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
