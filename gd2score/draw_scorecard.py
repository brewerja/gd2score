from svgwrite import Drawing
from svgwrite.shapes import Line, Rect
from svgwrite.text import Text
from svgwrite.container import Group

from .draw_runners import DrawRunners
from .constants import (ORIGIN_X, ORIGIN_Y, ATBAT_W, ATBAT_HT, NAME_W,
                        TEXT_HOP, SCORE_W, SEPARATION,
                        AWAY_NAME_X, AWAY_SCORING_X,
                        HOME_NAME_X, HOME_SCORING_X, HASH_SEP, HASH_LEN, flip)


class DrawScorecard:
    def __init__(self):
        self.runner_drawer = DrawRunners()

    def draw(self, game):
        self.game = game
        self.players = game.players

        self.dwg = Drawing(debug=True, profile='full')
        self.dwg.add_stylesheet('static/style.css', 'styling')

        self.draw_team_boxes()
        self.draw_inning_separators_and_numbers()
        self.draw_game()
        self.draw_pitcher_hash_marks()
        self.draw_pitcher_names()

        return self.dwg

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
        away_ht = sum(
            self.get_inning_height(inning) for inning in
            self.game.innings)
        away_team = self.get_team_box('away_team', away_ht)

        home_ht = away_ht
        if self.is_no_final_bottom():
            final_inning = self.game.innings[-1]
            home_ht = away_ht - len(final_inning.halves[0].atbats) * ATBAT_HT
        home_team = self.get_team_box('home_team', home_ht)
        flip(home_team)

        self.dwg.add(away_team)
        self.dwg.add(home_team)

    def draw_inning_separators_and_numbers(self):
        y = ORIGIN_Y
        for i, inning in enumerate(self.game.innings[:-1]):
            inning_ht = self.get_inning_height(inning)
            y += inning_ht
            self.dwg.add(Line((ORIGIN_X, y), (ORIGIN_X + ATBAT_W, y),
                              class_='team-box'))
            self.draw_inning_number(i + 1, y - inning_ht / 2)
            if (i == len(self.game.innings) - 2 and self.is_no_final_bottom()):
                break
            self.dwg.add(Line((ORIGIN_X + ATBAT_W + SEPARATION, y),
                              (ORIGIN_X + 2 * ATBAT_W + SEPARATION, y),
                              class_='team-box'))

        inning_ht = self.get_inning_height(self.game.innings[-1])
        self.draw_inning_number(len(self.game.innings), y + inning_ht / 2)

    def draw_inning_number(self, num, y):
        self.dwg.add(Text(num,
                          x=[ORIGIN_X + ATBAT_W + SEPARATION / 2],
                          y=[y],
                          class_='inning-num', text_anchor='middle',
                          dominant_baseline='middle'))

    def draw_game(self):
        self.y = ORIGIN_Y + ATBAT_HT
        for inning in self.game.innings:
            self.draw_inning(inning)

    def draw_inning(self, inning):
        inning_start_y = self.y
        inning_end_y = 0
        for half_inning in inning.halves:
            self.y = inning_start_y
            self.draw_half_inning(half_inning)
            inning_end_y = max(inning_end_y, self.y)
        self.y = inning_end_y

    def draw_half_inning(self, half_inning):
        for atbat in half_inning.atbats:
            self.set_x_and_anchor(half_inning.num)
            is_home_team_batting = half_inning.num % 1.0
            self.draw_atbat(atbat, is_home_team_batting)
            self.y += ATBAT_HT

    def draw_atbat(self, atbat, is_home_team_batting):
        atbat_group = Group()
        atbat_group.set_desc(atbat.get_description())
        atbat_group.add(self.get_batter_name_text(atbat))
        atbat_group.add(self.get_scoring_text(atbat))
        self.runner_drawer.execute(self.y, atbat, atbat_group,
                                   is_home_team_batting)
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
        self.home_pitchers = [self.game.innings[0].halves[0].atbats[0].pitcher]
        self.away_pitchers = [self.game.innings[0].halves[1].atbats[0].pitcher]

        self.y = ORIGIN_Y
        self.draw_both_hashes()
        for inning in self.game.innings:
            inning_start = self.y
            for half_inning in inning.halves:
                for atbat in half_inning.atbats:
                    if (atbat.pitcher != self.home_pitchers[-1] and
                            atbat.pitcher != self.away_pitchers[-1]):
                        self.draw_hash(half_inning.num)
                        self.swap_pitcher(atbat.pitcher, half_inning.num)
                    self.y += ATBAT_HT
                self.y = inning_start
            self.y = (inning_start + self.get_inning_height(inning))

        self.draw_hash(1.0)
        if self.is_no_final_bottom():
            self.y = self.y - ATBAT_HT * len(inning.halves[0].atbats)
        self.draw_hash(1.5)

    def get_inning_height(self, inning):
        return ATBAT_HT * max(len(h.atbats) for h in inning.halves)

    def draw_both_hashes(self):
        self.draw_hash(1.0)
        self.draw_hash(1.5)

    def draw_hash(self, inning):
        line = Line((ORIGIN_X + ATBAT_W + HASH_SEP, self.y),
                    (ORIGIN_X + ATBAT_W + HASH_SEP + HASH_LEN, self.y))
        if self.is_home_team_batting(inning):
            flip(line)
            self.home_hash_ys.append(self.y)
            line['class'] = 'away-pitcher-hash'
        else:
            self.away_hash_ys.append(self.y)
            line['class'] = 'home-pitcher-hash'
        self.dwg.add(line)

    def swap_pitcher(self, pitcher, inning_num):
        if self.is_home_team_batting(inning_num):
            self.away_pitchers.append(pitcher)
        else:
            self.home_pitchers.append(pitcher)

    def is_no_final_bottom(self):
        return self.game.innings and not len(self.game.innings[-1].halves) == 2

    def draw_pitcher_names(self):
        self._draw_pitcher_names(self.away_hash_ys, False)
        self._draw_pitcher_names(self.home_hash_ys, True)

    def _draw_pitcher_names(self, y_array, flip):
        for i, y in enumerate(y_array[:-1]):
            y_t = (y + y_array[i + 1]) / 2
            if flip:
                x = ORIGIN_X + ATBAT_W + SEPARATION - HASH_SEP - HASH_LEN / 2
                pitcher_name = self.players[self.away_pitchers[i]]
            else:
                x = ORIGIN_X + ATBAT_W + HASH_SEP + HASH_LEN / 2
                pitcher_name = self.players[self.home_pitchers[i]]
            txt = Text(pitcher_name, x=[x], y=[y_t], text_anchor='middle',
                       dominant_baseline='middle')
            if flip:
                txt['id'] = 'away-pitcher-%02d' % i
                txt['class'] = 'away-pitcher-name'
                txt.rotate(-90, (x, y_t))
            else:
                txt['id'] = 'home-pitcher-%02d' % i
                txt['class'] = 'home-pitcher-name'
                txt.rotate(90, (x, y_t))

            self.dwg.add(txt)

    def is_home_team_batting(self, inning):
        return inning % 1.0
