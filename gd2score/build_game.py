import statsapi

from .parse_game import GameParser
from .enhance import GameEnhancer


class GameBuilder:
    def __init__(self):
        self.game_parser = GameParser()
        self.game_enhancer = GameEnhancer()

    def build(self, game_id):
        feed = statsapi.get('game', {'gamePk': game_id})
        plays = feed['liveData']['plays']['allPlays']
        game = self.game_parser.parse(plays)
        game.away = feed['gameData']['teams']['away']['fileCode']
        game.home = feed['gameData']['teams']['home']['fileCode']
        self.game_enhancer.execute(game)
        return game
