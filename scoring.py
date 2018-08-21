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

Scoring = namedtuple('Scoring', 'code result')


def get_scoring(ab):
    ab.des = re.sub('\s,(\w)', r', \1', ab.des)  # 5/12
    if ((ab.event == 'Strikeout' or ab.event == 'Strikeout - DP') and
        ('swinging' in ab.des or 'on a foul tip' in ab.des or
         'on a foul bunt' in ab.des or 'on a missed bunt' in ab.des)):
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
        print(ab.__dict__)
        return Scoring('BI', 'out')
    elif ab.event == 'Groundout' or ab.event == 'Bunt Groundout':
        g = re.search('grounds out(?:\s\w+)? to (\w+ baseman|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
        g = re.search('grounds out(?:\s\w+)?, (\w+ fielder|\w+ baseman|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Grounded Into DP':
        g = re.search('double play, (\w+ baseman|shortstop|pitcher|catcher)',
                      ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Forceout':
        g = re.search('ground(?:s)?(?:\sbunts)? into a force out, (?:fielded by\s)?(\w+ baseman|shortstop|pitcher|catcher)',
                      ab.des)
        if g:
            return Scoring('G' + POSITIONS[g.group(1)], 'out')
        g = re.search('(flies|lines|pops) into a force out, (?:fielded by\s)?(\w+ baseman|\w+ fielder|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)],
                           'out')
    elif ab.event == 'Sac Fly':
        g = re.search('sacrifice fly to (\w+ fielder|\w+ baseman|shortstop)', ab.des)
        if g:
            return Scoring('F' + POSITIONS[g.group(1)], 'out')
        g = re.search('sacrifice fly. Fielding error by (\w+ fielder)', ab.des)
        if g:  # 4/25
            return Scoring('E' + POSITIONS[g.group(1)], 'error')
    elif ab.event == 'Sac Fly DP' or ab.event == 'Sacrifice Bunt DP':
        g = re.search('(ground bunts|flies) into a sacrifice double play, (\w+ fielder|\w+ baseman|pitcher|catcher)',
                      ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)], 'out')
    elif ab.event == 'Sac Bunt':
        g = re.search('sacrifice bunt(?:,|\sto) (\w+ baseman|pitcher|catcher)', ab.des)
        if g:  # TODO: Sac bunt...G or P or F?
            return Scoring('B' + POSITIONS[g.group(1)], 'out')
        if 'hits a sacrifice bunt' in ab.des:
            return Scoring('SAC', 'out')
    elif ab.event == 'Flyout':
        g = re.search('flies out (?:\w+\s)?to (\w+ fielder|\w+ baseman)', ab.des)
        if g:
            return Scoring('F' + POSITIONS[g.group(1)], 'out')
        g = re.search('flies out, (\w+ fielder)', ab.des)
        if g:
            return Scoring('F' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Lineout' or ab.event == 'Bunt Lineout':
        g = re.search('lines out (?:\w+\s)?to (\w+ baseman|\w+ fielder|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('L' + POSITIONS[g.group(1)], 'out')
        g = re.search('lines out(?:\s\w+)?, (\w+ baseman|\w+ fielder|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('L' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Double Play':
        g = re.search("(pops|grounds|hit|flies|lines) into a(?:n unassisted|\sfielder's choice)? double play(?:\sin foul territory)?, (\w+ fielder|\w+ baseman|shortstop|pitcher|catcher)", ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)], 'out')
    elif ab.event == 'Triple Play':
        g = re.search("(pops|grounds|hit|flies|lines) into a(?:n unassisted|\sfielder's choice)? triple play(?:\sin foul territory)?, (\w+ fielder|\w+ baseman|shortstop|pitcher|catcher)", ab.des)
        if g:
            return Scoring(AIR_TYPES[g.group(1)] + POSITIONS[g.group(2)], 'out')
        pass
    elif ab.event == 'Pop Out' or ab.event == 'Bunt Pop Out':
        g = re.search('pops out (?:\w+\s)?to (\w+ baseman|shortstop|pitcher|catcher)', ab.des)
        if g:  # TODO: combine
            return Scoring('P' + POSITIONS[g.group(1)], 'out')
        g = re.search('pops out, (\w+ baseman|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('P' + POSITIONS[g.group(1)], 'out')
    elif ab.event == 'Runner Out':
        if 'picked off and caught stealing' in ab.des:
            return Scoring('POCS', 'out')
        elif 'picks off' in ab.des:
            return Scoring('PO', 'out')
        elif 'caught stealing' in ab.des:
            return Scoring('CS', 'out')
        elif 'out at' in ab.des:
            return Scoring('TOOTBLAN', 'out')
    elif ab.event == 'Single':
        g = re.search('(\w+ ball|line drive|pop up|bunt pop) to (\w+ fielder|\w+ baseman|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)] + POSITIONS[g.group(2)],
                           'on-base')
        g = re.search('line drive to (\w+ fielder|\w+ baseman|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring('L' + POSITIONS[g.group(1)], 'on-base')
        g = re.search('singles on a ground ball\.', ab.des)
        if g:  # runner hit by ball 4/24
            return Scoring('S', 'on-base')
    elif ab.event == 'Double':
        g = re.search('(\w+ ball|pop up|line drive) to (\w+ fielder|\w+ baseman|shortstop)', ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)] + POSITIONS[g.group(2)], 'on-base')
        if 'ground-rule' in ab.des:
            if 'line drive' in ab.des:
                return Scoring('L', 'on-base')
            elif 'fly ball' in ab.des:
                return Scoring('F', 'on-base')
            elif 'ground ball' in ab.des:
                return Scoring('G', 'on-base')
    elif ab.event == 'Triple':
        g = re.search('(\w+ ball|line drive|pop up) to (\w+ fielder|\w+ baseman|shortstop|pitcher|catcher)', ab.des)
        if g:
            return Scoring(HIT_BALLS[g.group(1)] + POSITIONS[g.group(2)], 'on-base')
    elif ab.event == 'Home Run':
        return Scoring('HR', 'on-base')
    elif ab.event == 'Hit By Pitch':
        return Scoring('HB', 'on-base')
    elif ab.event == 'Field Error':
        g = re.search('(?:interference|fielding|missed catch|throwing) error by (\w+ baseman|\w+ fielder|pitcher|shortstop|catcher)', ab.des)
        if g:
            return Scoring('E' + POSITIONS[g.group(1)], 'error')
    elif ab.event == 'Fielders Choice Out':
        g = re.search("reaches on a fielder's choice out, (\w+ baseman|pitcher|shortstop|catcher)", ab.des)
        if g:
            return Scoring('FC' + POSITIONS[g.group(1)], 'fc')
    elif ab.event == 'Fielders Choice':
        g = re.search("reaches on a fielder's choice, fielded by (\w+ baseman|shortstop|pitcher|catcher)", ab.des)
        if g:
            return Scoring('FC' + POSITIONS[g.group(1)], 'fc')
    elif ab.event == 'Fan interference':
        return Scoring('FI', 'on-base')  # Nearly impossible to parse 4/18
    else:
        print(ab.__dict__)
        raise Exception('New event type: %s' % ab.event)

    print(ab.__dict__)
    raise Exception('Parsing error')

