import xml.etree.ElementTree as ET


class Player:
    def __init__(self, id, first, last):
        self.id = id
        self.first = first
        self.last = last

    def __str__(self):
        uppers = ['%s.' % c for c in self.first if c.isupper()]
        return '%s %s' % (''.join(uppers), self.last)

    def __repr__(self):
        return self.__str__()


class PlayersParser:
    def __init__(self, xml):
        self.players = dict()
        self.parse_players(xml)

    def parse_players(self, xml):
        game = ET.fromstring(xml)

        for team in game:
            self.parse_team(team)

    def parse_team(self, team):
        if team.tag not in ['umpires']:
            for player in team:
                self.parse_player(player)

    def parse_player(self, player):
        if player.tag not in ['coach']:
            p = Player(int(player.attrib['id']), player.attrib['first'],
                       player.attrib['last'])
            self.players[p.id] = p


if __name__ == '__main__':
    with open('players.xml') as f:
        for player in PlayersParser(f.read()).players.values():
            print('%d %s' % (player.id, player))
