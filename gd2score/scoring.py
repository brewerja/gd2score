import re
from collections import namedtuple

POSITIONS = {
    'pitcher': '1',
    'catcher': '2',
    'first baseman': '3',
    'second baseman': '4',
    'third baseman': '5',
    'shortstop': '6',
    'left fielder': '7',
    'center fielder': '8',
    'right fielder': '9',
}

HIT_BALLS = {
    'bunt pop': 'P',
    'pop up': 'P',
    'line drive': 'L',
    'fly ball': 'F',
    'ground ball': 'G',
}

AIR_TYPES = {
    'ground bunts': 'G',
    'grounds': 'G',
    'pops': 'P',
    'lines': 'L',
    'flies': 'F',
    'hit': 'H',
}

OUT_TYPES = {
    'pops out': 'P',
    'flies out': 'F',
    'lines out': 'L',
    'grounds out': 'G',
}

POS = '(\w+ fielder|\w+ baseman|shortstop|pitcher|catcher)'
ERROR_TYPES = '(?:interference|fielding|missed catch|throwing)'
OUT = '(%s)' % '|'.join(OUT_TYPES.keys())
AIR = '(%s)' % '|'.join(AIR_TYPES.keys())
HIT = '(%s)' % '|'.join(HIT_BALLS.keys())

Scoring = namedtuple('Scoring', 'code result')


def get_scoring(ab):
    ab.des = re.sub('\s,(\w)', r', \1', ab.des)  # 5/12  ' ,w' -> ', w'

    if ((ab.event == 'Strikeout' or ab.event == 'Strikeout - DP') and
        ('swinging' in ab.des or 'on a foul tip' in ab.des or
         'on a foul bunt' in ab.des or 'on a missed bunt' in ab.des or
         'ejected' in ab.des)):
        return Scoring('K', 'out')

    elif ((ab.event == 'Strikeout' or ab.event == 'Strikeout - DP') and
          'called out on' in ab.des):
        return Scoring('Kl', 'out')

    elif ab.event == 'Walk':
        return Scoring('W', 'on-base')

    elif ab.event == 'Intent Walk':
        return Scoring('IW', 'on-base')

    elif ab.event == 'Catcher Interference':
        g = re.search('reaches on catcher interference', ab.des)
        if g:
            return Scoring('CI', 'on-base')

    elif ab.event == 'Batter Interference':  # 4/1/2018, dp, weird
        return Scoring('BI', 'out')

    elif ab.event == 'Grounded Into DP':
        g = re.search('double play, ' + POS, ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')

    elif ab.event == 'Forceout':
        g = re.search(AIR + ' into a force out, (?:fielded by\s)?' + POS,
                      ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)],
                           'out')

    elif ab.event == 'Sac Fly':
        g = re.search('sacrifice fly(?:,| to) ' + POS, ab.des)
        if g:
            return Scoring('F' + POSITIONS[g.group(1)], 'out')
        g = re.search('sacrifice fly. Fielding error by (\w+ fielder)', ab.des)
        if g:  # 4/25
            return Scoring('E' + POSITIONS[g.group(1)], 'error')

    elif ab.event == 'Sac Fly DP' or ab.event == 'Sacrifice Bunt DP':
        g = re.search((AIR + ' into a sacrifice double play'
                       '(?: in foul territory)?, ' + POS), ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)],
                           'out')

    elif ab.event == 'Sac Bunt':
        g = re.search('sacrifice bunt(?:,|\sto) ' + POS, ab.des)
        if g:  # TODO: Sac bunt...G or P or F?
            return Scoring('B' + POSITIONS[g.group(1)], 'out')
        if 'hits a sacrifice bunt' in ab.des:
            return Scoring('SAC', 'out')

    elif ab.event in ('Flyout', 'Lineout', 'Bunt Lineout', 'Pop Out',
                      'Bunt Pop Out', 'Groundout', 'Bunt Groundout'):
        # ', ' or ' sharply, ' or ' sharply to ' or ' to '
        g = re.search(OUT + '(?:,\s|\s\w+,\s|\s\w+\sto\s|\sto\s)' + POS,
                      ab.des)
        if g:
            return Scoring(OUT_TYPES[g.group(1)] + POSITIONS[g.group(2)],
                           'out')

    elif ab.event == 'Double Play' or ab.event == 'Triple Play':
        g = re.search((AIR + " into a(?:n unassisted|\sfielder's choice)? " +
                       '(?:double|triple) play(?:\sin foul territory)?, ' +
                       POS), ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)],
                           'out')
        # 9/10/2015 and 9/22/17 single on the play
        g = re.search('Double play', ab.des)
        if g:
            return Scoring('DP', 'out')

    elif ab.event == 'Runner Out':
        if 'picked off and caught stealing' in ab.des:
            return Scoring('POCS', 'out')
        elif 'picks off' in ab.des:
            return Scoring('PO', 'out')
        elif 'caught stealing' in ab.des:
            return Scoring('CS', 'out')
        elif 'out at' in ab.des:
            return Scoring('TOOTBLAN', 'out')

    elif ab.event == 'Double' and 'ground-rule' in ab.des:
        g = re.search(HIT, ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)], 'on-base')

    elif ab.event == 'Single' or ab.event == 'Double' or ab.event == 'Triple':
        # 4/20/16 error on appeal play
        g = re.search(HIT + ' to ' + POS, ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)] + POSITIONS[g.group(2)],
                           'on-base')

        g = re.search('singles on a (\w+\s)?(\w+ \w+)\.', ab.des)
        if g:  # runner hit by ball 4/24/18 4/16,25/17
            return Scoring('S', 'on-base')

        g = re.search('doubles\.', ab.des)
        if g:  # 3/31/17
            return Scoring('D', 'on-base')

        if ab.event == 'Single':
            return Scoring('S', 'on-base')

    elif ab.event == 'Home Run':
        return Scoring('HR', 'on-base')

    elif ab.event == 'Hit By Pitch':
        return Scoring('HB', 'on-base')

    elif ab.event == 'Field Error':
        g = re.search(ERROR_TYPES + ' error by ' + POS, ab.des)
        if g:
            return Scoring('E' + POSITIONS[g.group(1)], 'error')

    elif ab.event == 'Fielders Choice Out' or ab.event == 'Fielders Choice':
        g = re.search(("reaches on a fielder's choice(?:\sout)?, " +
                       "(?:fielded by\s)?" + POS), ab.des)
        if g:
            return Scoring('FC' + POSITIONS[g.group(1)], 'fc')

    elif ab.event == 'Fan interference':
        if ab.outs == 3 or ab.batter not in [r.id for r in ab.runners]:
            return Scoring('FI', 'out')
        return Scoring('FI', 'on-base')  # Nearly impossible to parse 4/18

    else:
        print(ab.__dict__)
        raise Exception('New event type: %s' % ab.event)

    print(ab.__dict__)
    raise Exception('Parsing error')
