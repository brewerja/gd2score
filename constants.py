ORIGIN_X, ORIGIN_Y = 10, 10
ATBAT_W, ATBAT_HT = 210, 20
NAME_W = 100
TEXT_HOP = 5
SCORE_W = 25
SEPARATION = 160
BASE_L = (ATBAT_W - NAME_W - SCORE_W) / 4

AWAY_NAME_X = ORIGIN_X + NAME_W - TEXT_HOP
AWAY_SCORING_X = ORIGIN_X + NAME_W + SCORE_W / 2

HOME_NAME_X = ORIGIN_X + 2 * ATBAT_W + SEPARATION - NAME_W + TEXT_HOP
HOME_SCORING_X = HOME_NAME_X - TEXT_HOP - SCORE_W / 2

def flip(graphic):
    graphic.translate(SEPARATION + 2 * (ORIGIN_X + ATBAT_W), 0)
    graphic.scale(-1, 1)
