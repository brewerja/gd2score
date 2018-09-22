import copy
from itertools import groupby

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
SEPARATION = 160

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

        self.draw_team_boxes()
        self.draw_inning_separators()
        self.draw_game()
        self.draw_pitchers()

        self.dwg.save()

    def get_team_box(self, id, ht):
        box = Group()
        box['id'] = id
        box['class'] = 'team-box'
        box.add(Rect((ORIGIN_X, ORIGIN_Y), (ATBAT_W, ht)))
        box.add(Line((ORIGIN_X + NAME_W, ORIGIN_Y),
                     (ORIGIN_X + NAME_W, ORIGIN_Y + ht)))
        box.add(Line((ORIGIN_X + NAME_W + SCORE_W, ORIGIN_Y),
                     (ORIGIN_X + NAME_W + SCORE_W, ORIGIN_Y + ht)))
        return box

    def draw_team_boxes(self):
        away_ht = sum([max(len(inning.top), len(inning.bottom))
                       for inning in self.game.innings]) * ATBAT_HT
        away_team = self.get_team_box('away_team', away_ht)

        home_ht = away_ht
        if self.is_no_final_bottom():
            home_ht = away_ht - len(self.game.innings[-1].top) * ATBAT_HT
        home_team = self.get_team_box('home_team', home_ht)
        self.flip(home_team)

        self.dwg.add(away_team)
        self.dwg.add(home_team)

    def draw_inning_separators(self):
        y = ORIGIN_Y
        for i, inning in enumerate(self.game.innings[:-1]):
            y += ATBAT_HT * max(len(inning.top), len(inning.bottom))
            self.dwg.add(Line((ORIGIN_X, y), (ORIGIN_X + ATBAT_W, y),
                              class_='team-box'))
            if (i == len(self.game.innings) - 2 and
                    self.is_no_final_bottom()):
                break
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
        atbat_group.set_desc(atbat.get_description())
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
        for id, group in groupby(atbat.mid_pa_runners, lambda r: r.id):
            for i, runner in enumerate(
                    sorted(group, key=lambda r: r.event_num)):
                runner_group = self.build_rgroup(runner, i, atbat.inning)
                atbat_group.add(runner_group)

    def build_rgroup(self, runner, r_index, inning):
        line = self.get_rline(runner, r_index)
        line_end = self.get_runner_end(line, runner.out)

        if self.is_home_team_batting(inning):
            self.flip(line)
            self.flip(line_end)

        if runner.out and not self.is_line_vertical(line):
            line_end.rotate(45, self.get_line_end(line))

        return self.group_runner(line, line_end, runner.to_score)

    def get_rline(self, runner, r_index):
        x = ORIGIN_X + NAME_W + SCORE_W
        x_start = x + BASE_L * runner.start
        x_end = x + BASE_L * runner.end
        y_start = self.y - ATBAT_HT
        y_end = self.y - ATBAT_HT / 2
        if r_index != 0:
            y_start = y_end
        return Line((x_start, y_start), (x_end, y_end))

    def draw_runners(self, atbat, atbat_group):
        for runner in atbat.runners:
            if runner.id == atbat.batter:
                x = ORIGIN_X + NAME_W
                x_end = x + SCORE_W + BASE_L * runner.end
                line = Line((x, self.y), (x_end, self.y))
                line_end = self.get_runner_end(line, runner.out)
                if self.is_home_team_batting(atbat.inning):
                    self.flip(line)
                    self.flip(line_end)
            else:
                x = ORIGIN_X + NAME_W + SCORE_W
                x_start = x + BASE_L * runner.start
                x_end = x + BASE_L * runner.end
                y_start = self.y - ATBAT_HT
                # TODO: no longer using id, does this fully solve all cases?
                mid_pa_runners = [r for r in atbat.mid_pa_runners
                                  if not r.out and r.end == runner.start]
                if mid_pa_runners:
                    x_start = x + BASE_L * max([r.end for r in mid_pa_runners])
                    y_start = self.y - ATBAT_HT / 2
                line = Line((x_start, y_start), (x_end, self.y))
                line_end = self.get_runner_end(line, runner.out)
                if self.is_home_team_batting(atbat.inning):
                    self.flip(line)
                    self.flip(line_end)
                if runner.out:
                    line_end.rotate(45, (x_end, self.y))

            runner_group = self.group_runner(line, line_end, runner.to_score)
            atbat_group.add(runner_group)

    def group_runner(self, line, line_end, to_score):
        runner_group = Group()
        runner_group.add(line)
        runner_group.add(line_end)
        if to_score:
            runner_group['class'] = 'runner to-score'
        else:
            runner_group['class'] = 'runner'
        return runner_group

    def get_runner_end(self, line, is_out):
        x, y = self.get_line_end(line)
        if is_out:
            g = Group()
            g.add(Line((x - 3, y - 3), (x + 3, y + 3)))
            g.add(Line((x - 3, y + 3), (x + 3, y - 3)))
            return g
        else:
            return Circle((x, y), 2)

    def is_line_vertical(self, line):
        return line.attribs['x1'] == line.attribs['x2']

    def get_line_end(self, line):
        return line.attribs['x2'], line.attribs['y2']

    def flip(self, graphic):
        graphic.translate(SEPARATION + 2 * (ORIGIN_X + ATBAT_W), 0)
        graphic.scale(-1, 1)

    def is_home_team_batting(self, inning):
        return inning % 1.0

    def draw_pitchers(self):
        self.away_hash_ys = []
        self.home_hash_ys = []

        self.y = ORIGIN_Y
        self.draw_both_hashes()
        for inning in self.game.innings:
            inning_start = self.y
            for half_inning in [inning.top, inning.bottom]:
                for atbat in half_inning:
                    for action in atbat.actions:
                        if action.event == 'Pitching Substitution':
                            self.draw_hash(atbat.inning)
                    self.y += ATBAT_HT
                self.y = inning_start
            self.y = (inning_start +
                      ATBAT_HT * max(len(inning.top), len(inning.bottom)))

        self.draw_hash(1.0)
        if self.is_no_final_bottom():
            self.y = self.y - ATBAT_HT * len(inning.top)
        self.draw_hash(1.5)

        self.draw_pitcher_names(self.away_hash_ys, False)
        self.draw_pitcher_names(self.home_hash_ys, True)

    def draw_pitcher_names(self, y_array, flip):
        for i, y in enumerate(y_array):
            if i == len(y_array) - 1:
                break
            y_t = (y + y_array[i + 1]) / 2
            if flip:
                x = ORIGIN_X + ATBAT_W + SEPARATION - 24
                pitcher_name = self.players[self.game.away_pitchers[i]]
            else:
                x = ORIGIN_X + ATBAT_W + 24
                pitcher_name = self.players[self.game.home_pitchers[i]]
            txt = Text(pitcher_name, x=[x], y=[y_t], text_anchor='middle',
                       alignment_baseline='middle')
            txt['class'] = 'pitcher-name'
            if flip:
                txt['id'] = 'away-pitcher-%02d' % i
                txt.rotate(-90, (x, y_t))
            else:
                txt['id'] = 'home-pitcher-%02d' % i
                txt.rotate(90, (x, y_t))

            self.dwg.add(txt)

    def draw_hash(self, inning):
        line = Line((ORIGIN_X + ATBAT_W + 20, self.y),
                    (ORIGIN_X + ATBAT_W + 30, self.y))
        if self.is_home_team_batting(inning):
            self.flip(line)
            self.home_hash_ys.append(self.y)
            index = len(self.home_hash_ys) - 1
            line['id'] = 'home-pitcher-hash-%02d' % index
        else:
            self.away_hash_ys.append(self.y)
            index = len(self.away_hash_ys) - 1
            line['id'] = 'away-pitcher-hash-%02d' % index
        line['class'] = 'pitcher-hash'
        self.dwg.add(line)

    def draw_both_hashes(self):
        self.draw_hash(1.0)
        self.draw_hash(1.5)

    def is_no_final_bottom(self):
        return self.game.innings and not self.game.innings[-1].bottom
