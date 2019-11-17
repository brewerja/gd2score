import re
import logging

import statsapi

from .models import Runner, Player
from .runner_highlighter import RunnerHighlighter


class GameEnhancer:
    def __init__(self):
        self.runner_highlighter = RunnerHighlighter()

    def execute(self, game):
        self.players = {}
        self.players[0] = Player(0, 'Held Runner')

        for inning in game:
            for half_inning in inning:
                self.fix_half_inning(half_inning)
                self.runner_highlighter.highlight(half_inning)

        game.players = self.players

    def fix_half_inning(self, half_inning):
        """Adds missing runner tags, and resolves the ending bases of runners
        with empty end tags."""
        outs = 0
        active_runners = []
        for atbat in half_inning:
            self.parse_player(atbat.batter)
            self.parse_player(atbat.pitcher)

            self.hold_runners(active_runners, atbat)

            active_runners = [r for r in atbat.runners
                              if not r.out and r.end != 4]
            outs = atbat.outs

    def parse_player(self, id):
        """Looks up name information for player id, adds to cache"""
        if id not in self.players:
            response = statsapi.get('person', {'personId': id})
            # name = response['people'][0]['initLastName']
            name = response['people'][0]['initLastName']
            self.players[id] = Player(id, name)

    def hold_runners(self, active_runners, atbat):
        """The schema only represents runner movement. We need a record in each
        atbat even when the runners hold. This algorithm doesn't worry about
        who the runners are and so it creates dummy runners."""
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
