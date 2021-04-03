LOGO_URL = 'https://www.mlbstatic.com/team-logos/team-cap-on-light/'
CODE = {
'ana': 108,
'ari': 109,
'bal': 110,
'bos': 111,
'chc': 112,
'cin': 113,
'cle': 114,
'col': 115,
'det': 116,
'hou': 117,
'kc': 118,
'la': 119,
'was': 120,
'nym': 121,
'oak': 133,
'pit': 134,
'sd': 135,
'sea': 136,
'sf': 137,
'stl': 138,
'tb': 139,
'tex': 140,
'tor': 141,
'min': 142,
'phi': 143,
'atl': 144,
'cws': 145,
'mia': 146,
'nyy': 147,
'mil': 158
}

def get_logo(team):
    return LOGO_URL + str(CODE[team]) + '.svg'
