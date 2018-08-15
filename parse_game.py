import xml.etree.ElementTree as ET


def parse_game(xml):
    game = ET.fromstring(xml)

    for inning in game:
        parse_inning(inning)


def parse_inning(inning):
    next = 'N' if inning.attrib['next'] == 'N' else ''
    print('Inning: ' + inning.attrib['num'] + ' ' + next)

    for half_inning in inning:
        parse_half_inning(half_inning)


def parse_half_inning(half_inning):
    print(' - ' + half_inning.tag)

    for step in half_inning:
        parse_step(step)


def parse_step(step):
    if step.tag == 'atbat':
        parse_atbat(step)
    elif step.tag == 'action':
        parse_action(step)
    else:
        raise Exception('Unknown step type')


def parse_atbat(atbat):
    print('  - %s (%s) %s' % (atbat.tag, atbat.attrib['event_num'],
                              atbat.attrib['des']))
    for child in atbat:
        if child.tag == 'runner':
            parse_runner(child)
        elif child.tag in ['pitch', 'po']:
            pass
        else:
            raise Exception('Unknown atbat step type: %s' % child.tag)


def parse_action(action):
    print('  - %s (%s) %s' % (action.tag, action.attrib['event_num'],
                              action.attrib['des']))


def parse_runner(runner):
    print('   - ' + runner.tag + ' ' + str(runner.attrib))


if __name__ == '__main__':
    parse_game('inning_all.xml')
