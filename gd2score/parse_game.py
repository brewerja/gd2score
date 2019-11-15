import statsapi

from .models import Game, Inning, HalfInning, Action, AtBat, Runner, Player
from .enhance import GameEnhancer
from .draw_scorecard import DrawScorecard


class GameParser:
    def parse(self, game_dict):
        game_id = game_dict['game_id']

        game = Game()
        # Used later for logo lookups
        game.away = self.get_team_code(game_dict['away_id'])
        game.home = self.get_team_code(game_dict['home_id'])

        active_inning = None
        active_half = None
        top_bottom = 'top'

        pbp = statsapi.get('game_playByPlay', {'gamePk': game_id})
        for play in pbp['allPlays']:
            inning_num = int(play['about']['inning'])
            if not active_inning or active_inning.num != inning_num:
                active_inning = Inning(inning_num)
                game.add_inning(active_inning)

            if not active_half or top_bottom != play['about']['halfInning']:
                top_bottom = play['about']['halfInning']
                active_half = HalfInning()
                active_inning.add_half(active_half)

            ab = AtBat(int(play['atBatIndex'] + 1),
                       int(play['atBatIndex'] + 1),
                       int(play['matchup']['batter']['id']),
                       play['result']['description'],
                       play['result']['eventType'],
                       int(play['matchup']['pitcher']['id']),
                       int(play['count']['outs']),
                       int(play['result']['homeScore']),
                       int(play['result']['awayScore']))

            self.parse_runners(ab, play)
            active_half.add_atbat(ab)

        return game

    def parse_runners(self, ab, play):
        runner_index = set(play['runnerIndex'])
        for i, runner in enumerate(play['runners']):
            mvmt = runner['movement']
            start = self.get_base(mvmt['start'])
            end = self.get_base(mvmt['end'])
            if not start and not end:
                continue
            if mvmt['outBase']:
                end = self.get_base(mvmt['outBase'])

            # Runners that advance multiple bases are listed for each base they
            # advance. Only create one Runner object per person.
            already_added = False
            play_index = int(runner['details']['playIndex'])
            runner_id = runner['details']['runner']['id']
            for ab_runner in ab.runners:
                if (ab_runner.id == runner_id and
                    ab_runner.event_num == play_index):
                        assert end > ab_runner.end
                        ab_runner.end = end  # Increase end
                        already_added = True
                        break

            if not already_added:
                r = Runner(runner_id, start, end, play_index)
                r.to_score = runner['details']['isScoringEvent']
                r.out = mvmt['isOut']

                if i in runner_index:
                    ab.add_atbat_runner(r)
                else:
                    ab.add_mid_pa_runner(r)

    def get_base(self, base):
        if not base:
            return 0
        elif base == 'score':
            return 4
        else:
            return int(base[0])

    def get_team_code(self, team_id):
        team = statsapi.get('team', {'teamId': team_id})['teams'][0]
        return team['teamCode']
