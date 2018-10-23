ORIGIN_X, ORIGIN_Y = 10, 50
ATBAT_W, ATBAT_HT = 210, 20
NAME_W = 100
TEXT_HOP = 5
SCORE_W = 25
SEPARATION = 160

AWAY_NAME_X = ORIGIN_X + NAME_W - TEXT_HOP
AWAY_SCORING_X = ORIGIN_X + NAME_W + SCORE_W / 2

HOME_NAME_X = ORIGIN_X + 2 * ATBAT_W + SEPARATION - NAME_W + TEXT_HOP
HOME_SCORING_X = HOME_NAME_X - TEXT_HOP - SCORE_W / 2

BASE_L = (ATBAT_W - NAME_W - SCORE_W) / 4
CIRCLE_R = 1.5
X_SIZE = 3
OUT_SHORTEN = 10

HASH_SEP = 20
HASH_LEN = 10


def flip(graphic):
    graphic.translate(SEPARATION + 2 * (ORIGIN_X + ATBAT_W), 0)
    graphic.scale(-1, 1)


LOGOS = {  # Those that differ
         'cha': 'cws',
         'chn': 'chc',
         'flo': 'fla',
         'kca': 'kc',
         'lan': 'la',
         'nya': 'nyy',
         'nyn': 'nym',
         'sfn': 'sf',
         'sln': 'stl',
         'sdn': 'sd',
         'tba': 'tb',
         'aas': 'al',
         'nas': 'nl',
         }
