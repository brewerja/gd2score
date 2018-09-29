from itertools import groupby
import math

from svgwrite.shapes import Circle, Line
from svgwrite.container import Group

from constants import (ORIGIN_X, ATBAT_HT, NAME_W, SCORE_W, BASE_L, CIRCLE_R,
                       X_SIZE, OUT_SHORTEN, flip)


class DrawRunners:
    def execute(self, y, atbat, atbat_group, is_home_team_batting):
        self.y = y
        self.atbat = atbat
        self.atbat_group = atbat_group
        self.is_home_team_batting = is_home_team_batting
        self.draw_runners()

    def draw_runners(self):
        self.draw_mid_pa_runners()
        self.draw_atbat_result_runners()

    def draw_mid_pa_runners(self):
        num_events = len(self.get_mid_pa_event_num_set())
        for i, (event_num, group) in enumerate(
                groupby(self.atbat.mid_pa_runners, lambda r: r.event_num)):
            for runner in sorted(list(group), key=lambda r: r.end):
                line = self.get_mid_pa_runner_line(runner, i, num_events)
                runner_group = self.finalize_runner_line(line, runner)
                self.atbat_group.add(runner_group)

    def get_mid_pa_event_num_set(self):
        return set([r.event_num for r in self.atbat.mid_pa_runners])

    def draw_atbat_result_runners(self):
        for runner in self.atbat.runners:
            if runner.id == self.atbat.batter:
                line = self.get_batter_runner_line(runner)
            else:
                line = self.get_baserunner_line(runner)
            runner_group = self.finalize_runner_line(line, runner)
            self.atbat_group.add(runner_group)

    def get_mid_pa_runner_line(self, runner, i, num_events):
        x = ORIGIN_X + NAME_W + SCORE_W
        x_start = x + BASE_L * runner.start
        x_end = x + BASE_L * runner.end
        y_step = ATBAT_HT / 2 / num_events
        y_start = self.y - ATBAT_HT + i * y_step
        y_end = y_start + y_step
        return Line((x_start, y_start), (x_end, y_end))

    def get_batter_runner_line(self, runner):
        x_start = ORIGIN_X + NAME_W
        x_end = x_start + SCORE_W + BASE_L * runner.end
        return Line((x_start, self.y), (x_end, self.y))

    def get_baserunner_line(self, runner):
        x = ORIGIN_X + NAME_W + SCORE_W
        x_start = x + BASE_L * runner.start
        x_end = x + BASE_L * runner.end
        y_start = self.y - ATBAT_HT
        mid_pa_runner = self.get_mid_pa_runner_to_use(runner.start)
        if mid_pa_runner:
            x_start = x + BASE_L * mid_pa_runner.end
            y_start = self.y - ATBAT_HT / 2
        return Line((x_start, y_start), (x_end, self.y))

    def get_mid_pa_runner_to_use(self, mid_pa_runner_end):
        if self.atbat.mid_pa_runners:
            last_event_num = max(self.get_mid_pa_event_num_set())
            mid_pa_runners = [r for r in self.atbat.mid_pa_runners
                              if not r.out and r.end == mid_pa_runner_end and
                              r.event_num == last_event_num]
            assert(len(mid_pa_runners) in (0, 1))
            if mid_pa_runners:
                return mid_pa_runners[0]

    def finalize_runner_line(self, line, runner):
        """(1) Draw end, (2) flip if necessary, (3) rotate end if necessary,
        (4) group together the line and the end, (5) add to_score flag."""
        if runner.out:
            self.shorten_line(line)
        line_end = self.get_runner_end(line, runner.out)
        if self.is_home_team_batting:
            flip(line)
            flip(line_end)
        if runner.out:
            self.rotate_line_end(line_end, line)
        return self.group_runner(line, line_end, runner.to_score)

    def shorten_line(self, line):
        if not self.is_line_vertical(line):
            x, y = self.get_line_start(line)
            length = self.get_line_length(line) - OUT_SHORTEN
            degrees = self.get_line_angle(line)
            new_x = x + length * math.cos(math.radians(degrees))
            new_y = y + length * math.sin(math.radians(degrees))
        else:
            x, y = self.get_line_end(line)
            new_x = x
            new_y = self.get_line_end(line)[1] - OUT_SHORTEN
        line.attribs['x2'], line.attribs['y2'] = new_x, new_y

    def rotate_line_end(self, line_end, line):
        if not self.is_line_vertical(line):
            degrees = self.get_line_angle(line)
            line_end.rotate(degrees, self.get_line_end(line))

    def get_line_angle(self, line):
        x1, y1 = self.get_line_start(line)
        x2, y2 = self.get_line_end(line)
        return math.degrees(math.atan((y2 - y1) / (x2 - x1)))

    def get_runner_end(self, line, is_out):
        x, y = self.get_line_end(line)
        if is_out:
            g = Group()
            g.add(Line((x - X_SIZE, y - X_SIZE), (x + X_SIZE, y + X_SIZE)))
            g.add(Line((x - X_SIZE, y + X_SIZE), (x + X_SIZE, y - X_SIZE)))
            return g
        else:
            return Circle((x, y), CIRCLE_R)

    def group_runner(self, line, line_end, to_score):
        runner_group = Group()
        runner_group.add(line)
        runner_group.add(line_end)
        if to_score:
            runner_group['class'] = 'runner to-score'
        else:
            runner_group['class'] = 'runner'
        return runner_group

    def is_line_vertical(self, line):
        return line.attribs['x1'] == line.attribs['x2']

    def get_line_start(self, line):
        return line.attribs['x1'], line.attribs['y1']

    def get_line_end(self, line):
        return line.attribs['x2'], line.attribs['y2']

    def get_line_length(self, line):
        x_start, y_start = self.get_line_start(line)
        x_end, y_end = self.get_line_end(line)
        return math.hypot(x_end - x_start, y_end - y_start)
