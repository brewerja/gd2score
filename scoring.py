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
    'pop up': 'P',
    'line drive': 'L',
    'fly ball': 'F',
    'ground ball': 'G',
}

AIR_TYPES = {
    'lines': 'L',
    'flies': 'F',
}

Scoring = namedtuple('Scoring', 'code result')


def get_scoring(ab):
    if ab.event == 'Strikeout' and ('swinging' in ab.des or 'on a foul tip'
                                    in ab.des or 'on a foul bunt' in ab.des):
        return Scoring('K', 'out')
    if ab.event == 'Strikeout' and 'called out on' in ab.des:
        return Scoring('Kl', 'out')
    if ab.event == 'Strikeout - DP':
        if 'swinging' in ab.des:
            return Scoring('K', 'out')
    elif ab.event == 'Walk':
        return Scoring('W', 'on-base')
    elif ab.event == 'Intent Walk':
        return Scoring('IW', 'on-base')
    elif ab.event == 'Groundout' or ab.event == 'Bunt Groundout':
        g = re.search('grounds out, (\w+ baseman|shortstop|pitcher)', ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
        g = re.search('grounds out(?:\s\w+)? to (\w+ baseman|pitcher)', ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
        g = re.search('grounds out(?:\s\w+)?, (\w+ baseman|shortstop|pitcher|catcher)',
                      ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Grounded Into DP':
        g = re.search('double play, (\w+? baseman|shortstop|pitcher|catcher)',
                      ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Forceout':
        g = re.search('grounds into a force out, (?:fielded by\s)?(\w+? baseman|shortstop|pitcher|catcher)',
                      ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Sac Fly':
        g = re.search('sacrifice fly to (\w+? fielder)', ab.des)
        if g:
            return Scoring('F' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Sac Bunt':
        g = re.search('sacrifice bunt(?:,|\sto) (\w+? baseman|pitcher|catcher)', ab.des)
        if g:  # TODO: Sac bunt...G or P or F?
            return Scoring('B' + POSITIONS[g.group(1)], 'out')
        if 'hits a sacrifice bunt' in ab.des:
            return Scoring('SAC', 'out')
    elif ab.event == 'Flyout':
        g = re.search('flies out (?:\w+\s)?to (\w+? fielder)', ab.des)
        if g:
            return Scoring('F' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Lineout' or ab.event == 'Bunt Lineout':
        g = re.search('lines out (?:\w+\s)?to (\w+? baseman|\w+? fielder|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('L' + POSITIONS[g.group(1)], 'out')
        g = re.search('lines out(?:\s\w+)?, (\w+? baseman|\w+? fielder|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('L' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Double Play':
        g = re.search('(flies|lines) into a(?:n unassisted)? double play, (\w+? fielder|\w+? baseman)', ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)], 'out')
    elif ab.event == 'Pop Out' or ab.event == 'Bunt Pop Out':
        g = re.search('pops out (?:\w+\s)?to (\w+? baseman|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('P' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Runner Out':
        if 'picked off and caught stealing' in ab.des:
            return Scoring('POCS', 'out')
        elif 'picks off' in ab.des:
            return Scoring('PO', 'out')
        elif 'caught stealing' in ab.des:
            return Scoring('CS', 'out')
        elif 'out at 3rd' in ab.des:
            return Scoring('TOOTBLAN', 'out')
    elif ab.event == 'Single':
        g = re.search('(\w+? ball|line drive) to (\w+? fielder|\w+? baseman|shortstop|pitcher)', ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)] + POSITIONS[g.group(2)],
                           'on-base')
        g = re.search('line drive to (\w+? fielder|\w+? baseman)', ab.des)
        if g:
            return Scoring('L' + POSITIONS[g.group(1)], 'on-base')
    elif ab.event == 'Double':
        g = re.search('(\w+? ball|pop up|line drive) to (\w+ fielder|\w+ baseman|shortstop)', ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)] + POSITIONS[g.group(2)], 'on-base')
        if 'ground-rule' in ab.des and 'line drive' in ab.des:
            return Scoring('L', 'on-base')
        if 'ground-rule' in ab.des and 'fly ball' in ab.des:
            return Scoring('F', 'on-base')
    elif ab.event == 'Triple':
        g = re.search('(\w+? ball|line drive) to (\w+ fielder)', ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)] + POSITIONS[g.group(2)], 'on-base')
    elif ab.event == 'Home Run':
        return Scoring('HR', 'on-base')
    elif ab.event == 'Hit By Pitch':
        return Scoring('HB', 'on-base')
    elif ab.event == 'Field Error':
        g = re.search('(?:fielding|missed catch|throwing) error by (\w+? baseman|pitcher|shortstop)', ab.des)
        if g:
            return Scoring('E' + POSITIONS[g.group(1)], 'error')
    elif ab.event == 'Fielders Choice Out':
        g = re.search("reaches on a fielder's choice out, (\w+ baseman|pitcher|shortstop|catcher)", ab.des)
        if g:
            return Scoring('FC' + POSITIONS[g.group(1)], 'fc')
    elif ab.event == 'Fielders Choice':
        g = re.search("reaches on a fielder's choice, fielded by (\w+ baseman|shortstop)", ab.des)
        if g:
            return Scoring('FC' + POSITIONS[g.group(1)], 'fc')

        

    print(ab.__dict__)
    raise Exception('NOT MATCHED')

