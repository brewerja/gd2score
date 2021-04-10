import re
from collections import namedtuple

POSITIONS = {
    'pitcher': '1',
    'catcher': '2',
    '1B': '3',
    'first baseman': '3',
    '2B': '4',
    'second baseman': '4',
    '3B': '5',
    'third baseman': '5',
    'SS': '6',
    'shortstop': '6',
    'left fielder': '7',
    'center fielder': '8',
    'right fielder': '9',
    'fan interference': '',
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

POS = '(\w+ fielder|\w+ baseman|shortstop|pitcher|catcher|fan interference|1B|2B|3B)'
ERROR_TYPES = '(?:interference|fielding|missed catch|throwing|reaches on an)'
OUT = '(%s)' % '|'.join(OUT_TYPES.keys())
AIR = '(%s)' % '|'.join(AIR_TYPES.keys())
HIT = '(%s)' % '|'.join(HIT_BALLS.keys())

Scoring = namedtuple('Scoring', 'code result')


def get_scoring(ab):
    # hitData.location
    ab.des = re.sub('\s,(\w)', r', \1', ab.des)  # 5/12  ' ,w' -> ', w'

    if (ab.event.startswith('strikeout') and
        ('swinging' in ab.des or 'on a foul tip' in ab.des or
         'on a foul bunt' in ab.des or 'on a missed bunt' in ab.des or
         'ejected' in ab.des)):
        return Scoring('K', 'out')

    elif ab.event.startswith('strikeout') and 'called out on' in ab.des:
        return Scoring('Kl', 'out')

    elif ab.event == 'walk':
        return Scoring('W', 'on-base')

    elif ab.event == 'intent_walk':
        return Scoring('IW', 'on-base')

    elif ab.event == 'catcher_interf':
        g = re.search('reaches on catcher interference', ab.des)
        if g:
            return Scoring('CI', 'error')

    elif ab.event == 'batter_interference':  # 4/1/2018, dp, weird
        return Scoring('BI', 'out')

    elif ab.event == 'grounded_into_double_play':
        g = re.search('double play, ' + POS, ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')

    elif ab.event == 'force_out':
        g = re.search(AIR + ' into a force out, (?:fielded by\s)?' + POS,
                      ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)],
                           'fc')

    elif ab.event == 'sac_fly':
        g = re.search('sacrifice fly(?:,| to) ' + POS, ab.des)
        if g:
            return Scoring('F' + POSITIONS[g.group(1)], 'out')
        g = re.search('sacrifice fly.\s+Fielding error by (\w+ fielder)', ab.des)
        if g:  # 4/25
            return Scoring('E' + POSITIONS[g.group(1)], 'error')

    elif (ab.event == 'sac_fly_double_play' or
          ab.event == 'sac_bunt_double_play'):
        g = re.search((AIR + ' into a sacrifice double play'
                       '(?: in foul territory)?, ' + POS), ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)],
                           'out')

    elif ab.event == 'sac_bunt':
        g = re.search('sacrifice bunt(?:,|\sto) ' + POS, ab.des)
        if g:  # TODO: Sac bunt...G or P or F?
            return Scoring('B' + POSITIONS[g.group(1)], 'out')
        if 'hits a sacrifice bunt' in ab.des:
            return Scoring('SAC', 'out')

    elif ab.event == 'field_out':
    #elif ab.event in ('Flyout', 'Lineout', 'Bunt Lineout', 'Pop Out',
    #                  'Bunt Pop Out', 'Groundout', 'Bunt Groundout'):
        # ', ' or ' sharply, ' or ' sharply to ' or ' to '
        g = re.search(OUT + '(?:,\s|\s\w+,\s|\s\w+\sto\s|\sto\s|\son\s)' + POS,
                      ab.des)
        if g:
            return Scoring(OUT_TYPES[g.group(1)] + POSITIONS[g.group(2)],
                           'out')
        g = re.search(OUT, ab.des)
        if g:
            return Scoring(OUT_TYPES[g.group(1)], 'out')

    elif ab.event == 'double_play' or ab.event == 'triple_play':
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

    elif ab.event.startswith('pickoff_caught_stealing'): # 2b, 3b, home
        return Scoring('POCS', 'fc')
    elif ab.event.startswith('pickoff_error'):
        return Scoring('PO', 'error')
    elif ab.event.startswith('pickoff'):
        return Scoring('PO', 'fc')
    elif ab.event.startswith('caught_stealing'):
        return Scoring('CS', 'fc')
    elif ab.event == 'runner_double_play':
        return Scoring('DP', 'out')

    elif ab.event == 'double' and 'ground-rule' in ab.des:
        g = re.search(HIT, ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)], 'on-base')

    elif ab.event in ('single', 'double', 'triple'):
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

        if ab.event == 'single':
            return Scoring('S', 'on-base')
        elif ab.event == 'double':
            return Scoring('D', 'on-base')
        elif ab.event == 'triple':
            return Scoring('T', 'on-base')


    elif ab.event == 'home_run':
        return Scoring('HR', 'on-base')

    elif ab.event == 'hit_by_pitch':
        return Scoring('HB', 'on-base')

    elif ab.event == 'field_error':
        g = re.search(ERROR_TYPES + ' error by ' + POS, ab.des)
        if g:
            return Scoring('E' + POSITIONS[g.group(1)], 'error')

    elif ab.event == 'fielders_choice_out':
        g = re.search(("(?:fielded by\s)?" + POS), ab.des)
        if g and g.group(1) in POSITIONS.keys():
            print(ab.__dict__)
            return Scoring('FC' + POSITIONS[g.group(1)], 'fc')
        g = re.search(("reaches on a fielder's choice(?:\sout)?, " +
                       "(?:fielded by\s)?" + POS), ab.des)
        if g:
            return Scoring('FC' + POSITIONS[g.group(1)], 'fc')

    elif ab.event.startswith('fielders_choice'):
        g = re.search(("reaches on a fielder's choice(?:\sout)?, " +
                       "(?:fielded by\s)?" + POS), ab.des)
        if g:
            return Scoring('FC' + POSITIONS[g.group(1)], 'fc')
        else:
            return Scoring('FC', 'fc')

    elif ab.event == 'fan_interference':
        if ab.outs == 3 or ab.batter not in [r.id for r in ab.runners]:
            return Scoring('FI', 'out')
        return Scoring('FI', 'on-base')  # Nearly impossible to parse 4/18

    elif ab.event == 'wild_pitch':
        return Scoring('WP', 'on-base')
    elif ab.event == 'passed_ball':
        return Scoring('PB', 'on-base')
    elif ab.event == 'Strikeout Double Play':
        return Scoring('K', 'out')

    elif ab.event.startswith('stolen_base'):
        return Scoring('', 'out')
    elif ab.event == 'runner_double_play':
        return Scoring('DP', 'out')
    elif ab.event == 'other_out':
        return Scoring('', 'out')
    elif ab.event == 'other_advance':
        return Scoring('', 'on-base')

    elif ab.event == 'defensive_switch':
        return Scoring('DS', 'on-base')
    elif ab.event == 'balk':
        return Scoring('BK', 'on-base')

    elif ab.event in ['game_advisory', 'pitching_substitution',
            'offensive_substitution', 'runner_placed']:
        return Scoring('', 'blank')

    else:
        print(ab.__dict__)
        raise Exception('New event type: %s' % ab.event)

    print(ab.__dict__)
    raise Exception('Parsing error')
