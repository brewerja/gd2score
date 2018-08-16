import xml.etree.ElementTree as ET

class GameParser:
    def __init__(self, xml):
        self.event_types = set()
        self.parse_game(xml)

    def parse_game(self, xml):
        game = ET.fromstring(xml)

        for inning in game:
            self.parse_inning(inning)

    def parse_inning(self, inning):
        next = 'N' if inning.attrib['next'] == 'N' else ''
        print('Inning: ' + inning.attrib['num'] + ' ' + next)

        for half_inning in inning:
            self.parse_half_inning(half_inning)

    def parse_half_inning(self, half_inning):
        print(' - ' + half_inning.tag)

        for step in half_inning:
            self.parse_step(step)

    def parse_step(self, step):
        self.event_types.add(step.attrib['event'])
        if step.tag == 'atbat':
            self.parse_atbat(step)
        elif step.tag == 'action':
            self.parse_action(step)
        else:
            raise Exception('Unknown step type')

    def parse_atbat(self, atbat):
        print('  - %s (%s) %s' % (atbat.tag, atbat.attrib['event_num'],
                                  atbat.attrib['des']))
        for child in atbat:
            if child.tag == 'runner':
                self.parse_runner(child)
            elif child.tag in ['pitch', 'po']:
                pass
            else:
                raise Exception('Unknown atbat step type: %s' % child.tag)

    def parse_action(self, action):
        print('  - %s (%s) %s' % (action.tag, action.attrib['event_num'],
                                  action.attrib['des']))

    def parse_runner(self, runner):
        print('   - ' + runner.tag + ' ' + str(runner.attrib))


if __name__ == '__main__':
    with open('inning_all.xml') as f:
        g = GameParser(f.read())
    print(g.event_types)
