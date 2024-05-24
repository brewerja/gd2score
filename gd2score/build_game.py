import statsapi

from .parse_game import GameParser
from .enhance import GameEnhancer
from .models import Player


class GameBuilder:
    def __init__(self):
        self.game_parser = GameParser()
        self.game_enhancer = GameEnhancer()

    def build(self, game_id):
        feed = statsapi.get("game", {"gamePk": game_id})
        game = self.game_parser.parse(feed["liveData"]["plays"]["allPlays"])
        game.away = feed["gameData"]["teams"]["away"]["fileCode"]
        game.home = feed["gameData"]["teams"]["home"]["fileCode"]
        game.players = self.parse_players(feed["gameData"]["players"])
        self.game_enhancer.execute(game)
        return game

    def parse_players(self, player_dict):
        players = {0: Player(0, "Held Runner")}
        for key, player in player_dict.items():
            id = player["id"]
            players[id] = Player(id, player["initLastName"])
        return players
