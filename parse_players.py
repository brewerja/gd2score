import re
import xml.etree.ElementTree as ET


class Player:
    def __init__(self, id, first, last):
        self.id = id
        if re.match('[A-Z]\.\s?[A-Z]\.\s*', first):
            # 'A.J.' --> 'A. J.'
            self.first = '%s %s' % (first[:2], first[2:])
        else:
            self.first = first
        self.last = last

    def full_name(self):
        return ' '.join((self.first, self.last))

    def __str__(self):
        uppers = ['%s.' % c for c in self.first if c.isupper()]
        return '%s %s' % (' '.join(uppers), self.last)

    def __repr__(self):
        return self.__str__()


class PlayersParser:
    def __init__(self, xml):
        self.players = dict()
        self.parse_players(xml)

    def parse_players(self, xml):
        for team in ET.fromstring(xml):
            self.parse_team(team)

    def parse_team(self, team):
        if team.tag not in ['umpires']:
            for player in team:
                self.parse_player(player)

    def parse_player(self, player):
        if player.tag == 'player':
            p = Player(int(player.attrib['id']), player.attrib['first'],
                       player.attrib['last'])
            self.players[p.id] = p


if __name__ == '__main__':
    with open('players.xml') as f:
        for player in PlayersParser(f.read()).players.values():
            print('%d %s' % (player.id, player))
