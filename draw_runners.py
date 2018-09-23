from itertools import groupby
from svgwrite.shapes import Circle, Line
from svgwrite.container import Group
import math

from constants import *


class DrawRunners:
    def __init__(self, y, atbat, atbat_group):
        self.y = y
        self.atbat_group = atbat_group
        self.is_home_team_batting = atbat.inning % 1.0

        self.draw_mid_pa_runners(atbat.mid_pa_runners)
        self.draw_atbat_result_runners(atbat)

    def draw_mid_pa_runners(self, mid_pa_runners):
        """Draw each runner's complete set of movements in event_num order."""
        for id, group in groupby(mid_pa_runners, lambda r: r.id):
            for i, runner in enumerate(
                    sorted(group, key=lambda r: r.event_num)):
                line = self.get_mid_pa_runner_line(runner, i == 0)
                runner_group = self.finalize_runner_line(line, runner)
                self.atbat_group.add(runner_group)

    def draw_atbat_result_runners(self, atbat):
        for runner in atbat.runners:
            if runner.id == atbat.batter:
                line = self.get_batter_runner_line(runner)
            else:
                # TODO: no longer using id, does this fully solve all cases?
                # TODO: is this ever more than one in number?
                mid_pa_runners = [r for r in atbat.mid_pa_runners
                                  if not r.out and r.end == runner.start]
                line = self.get_baserunner_line(runner, mid_pa_runners)
            runner_group = self.finalize_runner_line(line, runner)
            self.atbat_group.add(runner_group)

    def get_mid_pa_runner_line(self, runner, is_first_advance_during_pa):
        x = ORIGIN_X + NAME_W + SCORE_W
        x_start = x + BASE_L * runner.start
        x_end = x + BASE_L * runner.end
        y_start = self.y - ATBAT_HT
        y_end = self.y - ATBAT_HT / 2
        if not is_first_advance_during_pa:
            y_start = y_end
        return Line((x_start, y_start), (x_end, y_end))

    def get_batter_runner_line(self, runner):
        x_start = ORIGIN_X + NAME_W
        x_end = x_start + SCORE_W + BASE_L * runner.end
        return Line((x_start, self.y), (x_end, self.y))

    def get_baserunner_line(self, runner, mid_pa_runners):
        x = ORIGIN_X + NAME_W + SCORE_W
        x_start = x + BASE_L * runner.start
        x_end = x + BASE_L * runner.end
        y_start = self.y - ATBAT_HT
        if mid_pa_runners:
            x_start = x + BASE_L * max([r.end for r in mid_pa_runners])
            y_start = self.y - ATBAT_HT / 2
        return Line((x_start, y_start), (x_end, self.y))

    def finalize_runner_line(self, line, runner):
        """(1) Draw end, (2) flip if necessary, (3) rotate end if necessary,
        (4) group together the line and the end, (5) add to_score flag."""
        line_end = self.get_runner_end(line, runner.out)
        if self.is_home_team_batting:
            self.flip(line)
            self.flip(line_end)
        if runner.out:
            self.rotate_line_end(line_end, line)
        return self.group_runner(line, line_end, runner.to_score)

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
            g.add(Line((x - 3, y - 3), (x + 3, y + 3)))
            g.add(Line((x - 3, y + 3), (x + 3, y - 3)))
            return g
        else:
            return Circle((x, y), 2)

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

    def flip(self, graphic):
        graphic.translate(SEPARATION + 2 * (ORIGIN_X + ATBAT_W), 0)
        graphic.scale(-1, 1)
