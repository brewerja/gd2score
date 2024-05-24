from .models import Runner
from .runner_highlighter import RunnerHighlighter


class GameEnhancer:
    def __init__(self):
        self.runner_highlighter = RunnerHighlighter()

    def execute(self, game):
        for inning in game:
            for half_inning in inning:
                self.fix_half_inning(half_inning)
                self.runner_highlighter.highlight(half_inning)

    def fix_half_inning(self, half_inning):
        """Adds missing runner tags, and resolves the ending bases of runners
        with empty end tags."""
        active_runners = []
        for atbat in half_inning:
            self.hold_runners(active_runners, atbat)
            active_runners = [r for r in atbat.runners if not r.out and r.end != 4]

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
