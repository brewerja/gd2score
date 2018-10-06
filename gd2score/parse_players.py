import xml.etree.ElementTree as ET

from .models import Player


class PlayersParser:
    def parse(self, xml):
        self.players = {}
        self.parse_players(xml)
        return self.players

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
