from svgwrite import Drawing
from svgwrite.shapes import Line, Rect
from svgwrite.text import Text
from svgwrite.container import Group

from draw_runners import DrawRunners
from constants import *


class DrawScorecard:
    def __init__(self, game, players, svg_filename):
        self.game = game
        self.players = players

        self.dwg = Drawing(svg_filename, debug=True, profile='full')
        self.dwg.add_stylesheet('style.css', 'styling')

        self.draw_team_boxes()
        self.draw_inning_separators()
        self.draw_game()
        self.draw_pitcher_hash_marks()
        self.draw_pitcher_names()

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
        flip(home_team)

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
        DrawRunners(self.y, atbat, atbat_group)
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

    def draw_pitcher_hash_marks(self):
        self.away_hash_ys = []
        self.home_hash_ys = []

        # Starting pitchers
        self.home_pitchers = [self.game.innings[0].top[0].pitcher]
        self.away_pitchers = [self.game.innings[0].bottom[0].pitcher]

        self.y = ORIGIN_Y
        self.draw_both_hashes()
        for inning in self.game.innings:
            inning_start = self.y
            for half_inning in [inning.top, inning.bottom]:
                for atbat in half_inning:
                    if (atbat.pitcher != self.home_pitchers[-1] and
                            atbat.pitcher != self.away_pitchers[-1]):
                        self.draw_hash(atbat.inning)
                        self.swap_pitcher(atbat)
                    self.y += ATBAT_HT
                self.y = inning_start
            self.y = (inning_start +
                      ATBAT_HT * max(len(inning.top), len(inning.bottom)))

        self.draw_hash(1.0)
        if self.is_no_final_bottom():
            self.y = self.y - ATBAT_HT * len(inning.top)
        self.draw_hash(1.5)

    def draw_both_hashes(self):
        self.draw_hash(1.0)
        self.draw_hash(1.5)

    def draw_hash(self, inning):
        line = Line((ORIGIN_X + ATBAT_W + 20, self.y),
                    (ORIGIN_X + ATBAT_W + 30, self.y))
        if self.is_home_team_batting(inning):
            flip(line)
            self.home_hash_ys.append(self.y)
            index = len(self.home_hash_ys) - 1
            line['id'] = 'home-pitcher-hash-%02d' % index
        else:
            self.away_hash_ys.append(self.y)
            index = len(self.away_hash_ys) - 1
            line['id'] = 'away-pitcher-hash-%02d' % index
        line['class'] = 'pitcher-hash'
        self.dwg.add(line)

    def swap_pitcher(self, atbat):
        if self.is_home_team_batting(atbat.inning):
            self.away_pitchers.append(atbat.pitcher)
        else:
            self.home_pitchers.append(atbat.pitcher)

    def is_no_final_bottom(self):
        return self.game.innings and not self.game.innings[-1].bottom

    def draw_pitcher_names(self):
        self._draw_pitcher_names(self.away_hash_ys, False)
        self._draw_pitcher_names(self.home_hash_ys, True)

    def _draw_pitcher_names(self, y_array, flip):
        for i, y in enumerate(y_array[:-1]):
            y_t = (y + y_array[i + 1]) / 2
            if flip:
                x = ORIGIN_X + ATBAT_W + SEPARATION - 24
                pitcher_name = self.players[self.away_pitchers[i]]
            else:
                x = ORIGIN_X + ATBAT_W + 24
                pitcher_name = self.players[self.home_pitchers[i]]
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

    def is_home_team_batting(self, inning):
        return inning % 1.0
