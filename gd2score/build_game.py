import statsapi

from .parse_game import GameParser
from .enhance import GameEnhancer


class GameBuilder:
    def __init__(self):
        self.game_parser = GameParser()
        self.game_enhancer = GameEnhancer()

    def build(self, game_dict):
        game_id = game_dict['game_id']
        pbp = statsapi.get('game_playByPlay', {'gamePk': game_id})
        game = self.game_parser.parse(pbp)
        # Used later for logo lookups
        game.away = self.get_team_code(game_dict['away_id'])
        game.home = self.get_team_code(game_dict['home_id'])
        self.game_enhancer.execute(game)
        return game

    def get_team_code(self, team_id):
        team = statsapi.get('team', {'teamId': team_id})['teams'][0]
        return team['teamCode']
