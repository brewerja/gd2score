import re
import urllib.request

from .parse_game import GameParser
from .parse_players import PlayersParser
from .enhance import GameEnhancer

GD2_URL = 'https://gd2.mlb.com/components/game/mlb'
GID_REGEX = ('^gid_(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})_'
             '[a-z]{6}_[a-z]{6}_\d$')


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
        g = re.match(GID_REGEX, gid)
        if not g:
            raise ValueError('Not a valid game id: %s' % gid)
        year, month, day = g.group('year'), g.group('month'), g.group('day')
        return ('%s/year_%s/month_%s/day_%s/%s/' %
                (GD2_URL, year, month, day, gid))

    def get_url(self, url):
        with urllib.request.urlopen(url) as response:
            return response.read()
