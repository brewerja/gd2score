class RunnerHighlighter:
    def highlight(self, half_inning):
        self.bases_scored_from = []
        for atbat in reversed(half_inning.atbats):
            self.bases_new = []
            self.parse_atbat_ending_runners(atbat)
            self.parse_mid_pa_runners(atbat)
            self.bases_scored_from = self.bases_new

    def parse_atbat_ending_runners(self, atbat):
        for runner in atbat.runners:
            if ((runner.end in self.bases_scored_from or
                 runner.end == 4) and not runner.out):
                self.mark_and_save(runner)

    def parse_mid_pa_runners(self, atbat):
        for runner in sorted(atbat.mid_pa_runners,
                             key=lambda r: r.event_num, reverse=True):
            if runner.end in self.bases_new and not runner.out:
                self.bases_new.remove(runner.end)
                self.mark_and_save(runner)
            elif runner.end == 4 and not runner.out:
                self.mark_and_save(runner)

    def mark_and_save(self, runner):
        runner.to_score = True
        if runner.start != 0:
            self.bases_new.append(runner.start)
