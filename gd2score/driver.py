import urllib.request

from .parse_game import GameParser
from .parse_players import PlayersParser
from .enhance import GameEnhancer

GD2_URL = 'https://gd2.mlb.com/components/game/mlb'


class GameBuilder:
    def __init__(self):
        self.game_parser = GameParser()
        self.players_parser = PlayersParser()
        self.game_enhancer = GameEnhancer()

    def build(self, game_id):
        game_url = self.get_game_url(game_id)
        players = self.parse_players(game_url)
        game = self.parse_game(game_url)
        game.players = players
        self.game_enhancer.execute(game)
        return game

    def parse_players(self, game_url):
        players_xml = self.get_url(game_url + 'players.xml')
        return self.players_parser.parse(players_xml)

    def parse_game(self, game_url):
        game_xml = self.get_url(game_url + 'inning/inning_all.xml')
        return self.game_parser.parse(game_xml)    
    
    def get_game_url(self, gid):
        p = gid.split('_')
        return ('%s/year_%04d/month_%02d/day_%02d/%s/' %
                (GD2_URL, int(p[1]), int(p[2]), int(p[3]), gid))

    def get_url(self, url):
        with urllib.request.urlopen(url) as response:
            return response.read()

