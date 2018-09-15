import copy
import logging

from svgwrite import Drawing
from svgwrite.shapes import Circle, Line, Rect
from svgwrite.text import Text
from svgwrite.container import Group

ORIGIN_X, ORIGIN_Y = 10, 10
ATBAT_W, ATBAT_HT = 210, 20
NAME_W = 100
TEXT_HOP = 5
SCORE_W = 25
BASE_L = (ATBAT_W - NAME_W - SCORE_W) / 4
SEPARATION = 30

AWAY_NAME_X = ORIGIN_X + NAME_W - TEXT_HOP
AWAY_SCORING_X = ORIGIN_X + NAME_W + SCORE_W / 2

HOME_NAME_X = ORIGIN_X + 2 * ATBAT_W + SEPARATION - NAME_W + TEXT_HOP
HOME_SCORING_X = HOME_NAME_X - TEXT_HOP - SCORE_W / 2


class Scorecard:
    def __init__(self, game, players, svg_filename):
        self.game = game
        self.players = players

        self.dwg = Drawing(svg_filename, debug=True, profile='full')
        self.dwg.add_stylesheet('style.css', 'styling')

        self.set_game_height()
        self.draw_team_boxes()
        self.draw_inning_separators()
        self.draw_game()

        self.dwg.save()

    def set_game_height(self):
        self.game_ht = sum([max(len(inning.top), len(inning.bottom))
                            for inning in self.game.innings]) * ATBAT_HT

    def get_team_box(self, id):
        box = Group()
        box['id'] = id
        box['class'] = 'team-box'
        box.add(Rect((ORIGIN_X, ORIGIN_Y), (ATBAT_W, self.game_ht)))
        box.add(Line((ORIGIN_X + NAME_W, ORIGIN_Y),
                     (ORIGIN_X + NAME_W, ORIGIN_Y + self.game_ht)))
        box.add(Line((ORIGIN_X + NAME_W + SCORE_W, ORIGIN_Y),
                     (ORIGIN_X + NAME_W + SCORE_W, ORIGIN_Y + self.game_ht)))
        return box

    def draw_team_boxes(self):
        away_team = self.get_team_box('away_team')
        home_team = self.get_team_box('home_team')
        self.flip(home_team)

        self.dwg.add(away_team)
        self.dwg.add(home_team)

    def draw_inning_separators(self):
        y = ORIGIN_Y
        for inning in self.game.innings:
            y += ATBAT_HT * max(len(inning.top), len(inning.bottom))
            self.dwg.add(Line((ORIGIN_X, y), (ORIGIN_X + ATBAT_W, y),
                              class_='team-box'))
            self.dwg.add(Line((ORIGIN_X + ATBAT_W + SEPARATION, y),
                              (ORIGIN_X + 2 * ATBAT_W + SEPARATION, y),
                              class_='team-box'))

    def draw_game(self):
        self.y = ORIGIN_Y + ATBAT_HT
        for inning in self.game.innings:
            self.draw_inning(inning)

    def draw_inning(self, inning):
        inning_start_y = self.y
        inning_end_y = 0
        for half_inning in [inning.top, inning.bottom]:
            self.y = inning_start_y
            self.draw_half_inning(half_inning)
            inning_end_y = max(inning_end_y, self.y)
        self.y = inning_end_y

    def draw_half_inning(self, half_inning):
        for atbat in half_inning:
            self.draw_atbat(atbat)
            self.y += ATBAT_HT

    def draw_atbat(self, atbat):
        self.set_x_and_anchor(atbat.inning)
        atbat_group = Group()
        atbat_group.set_desc(atbat.des)
        atbat_group.add(self.get_batter_name_text(atbat))
        atbat_group.add(self.get_scoring_text(atbat))
        self.draw_mid_pa_runners(atbat, atbat_group)
        self.draw_runners(atbat, atbat_group)
        self.dwg.add(atbat_group)

    def set_x_and_anchor(self, inning):
        if self.is_home_team_batting(inning):
            self.name_x = HOME_NAME_X
            self.scoring_x = HOME_SCORING_X
            self.name_anchor = 'start'
        else:
            self.name_x = AWAY_NAME_X
            self.scoring_x = AWAY_SCORING_X
            self.name_anchor = 'end'

    def get_batter_name_text(self, atbat):
        return Text(self.players.get(atbat.batter),
                    x=[self.name_x], y=[self.y - TEXT_HOP],
                    class_='batter-name',
                    text_anchor=self.name_anchor)

    def get_scoring_text(self, atbat):
        text = Text(atbat.scoring.code,
                    x=[self.scoring_x], y=[self.y - TEXT_HOP],
                    class_=atbat.scoring.result,
                    text_anchor='middle')
        if atbat.scoring.code == 'Kl':
            text.text = 'K'
            text.translate(2 * self.scoring_x, 0)
            text.scale(-1, 1)
        return text

    def draw_mid_pa_runners(self, atbat, atbat_group):
        runners_by_id = dict((runner.id, []) for runner
                             in atbat.mid_pa_runners)
        for runner in atbat.mid_pa_runners:
            runners_by_id[runner.id].append(runner)

        for id in runners_by_id.keys():
            for i, runner in enumerate(
                    sorted(runners_by_id[id], key=lambda r: r.id)):
                x = ORIGIN_X + NAME_W + SCORE_W
                x_start = x + BASE_L * runner.start
                x_end = x + BASE_L * runner.end
                y_start = self.y - ATBAT_HT
                y_end = self.y - ATBAT_HT / 2
                if i != 0:
                    y_start = y_end
                line = Line((x_start, y_start), (x_end, y_end))
                line_end = self.get_runner_end(x_end, y_end, runner.out)
                if self.is_home_team_batting(atbat.inning):
                    self.flip(line)
                    self.flip(line_end)
                if runner.out and x_end != x_start:
                    line_end.rotate(45, (x_end, y_end))
                atbat_group.add(line)
                atbat_group.add(line_end)

    def draw_runners(self, atbat, atbat_group):
        b_r = [r for r in atbat.runners if r.id == atbat.batter]
        for runner in atbat.runners:
            if runner.id == atbat.batter:
                x = ORIGIN_X + NAME_W
                x_end = x + SCORE_W + BASE_L * runner.end
                line = Line((x, self.y), (x_end, self.y))
                line_end = self.get_runner_end(x_end, self.y, runner.out)
                if self.is_home_team_batting(atbat.inning):
                    self.flip(line)
                    self.flip(line_end)
                atbat_group.add(line)
                atbat_group.add(line_end)
            else:
                x = ORIGIN_X + NAME_W + SCORE_W
                x_start = x + BASE_L * runner.start
                x_end = x + BASE_L * runner.end
                y_start = self.y - ATBAT_HT
                mid_pa_runners = [r for r in atbat.mid_pa_runners
                                  if not r.out and r.id == runner.id]
                if mid_pa_runners:
                    x_start = x + BASE_L * max([r.end for r in mid_pa_runners])
                    y_start = self.y - ATBAT_HT / 2
                line = Line((x_start, y_start), (x_end, self.y))
                line_end = self.get_runner_end(x_end, self.y, runner.out)
                if self.is_home_team_batting(atbat.inning):
                    self.flip(line)
                    self.flip(line_end)
                if runner.out:
                    line_end.rotate(45, (x_end, self.y))
                atbat_group.add(line)
                atbat_group.add(line_end)

    def get_runner_end(self, x, y, is_out):
        if is_out:
            g = Group()
            g.add(Line((x - 3, y - 3), (x + 3, y + 3)))
            g.add(Line((x - 3, y + 3), (x + 3, y - 3)))
            return g
        else:
            return Circle((x, y), 2)

    def flip(self, graphic):
        graphic.translate(SEPARATION + 2 * (ORIGIN_X + ATBAT_W), 0)
        graphic.scale(-1, 1)

    def is_home_team_batting(self, inning):
        return inning % 1.0
