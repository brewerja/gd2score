import re
from datetime import datetime, timedelta
import logging

import statsapi

from .build_game import GameBuilder
from .draw_scorecard import DrawScorecard


if __name__ == '__main__':
    logging.basicConfig(  # filename='parsing.log',
                        format='%(levelname)s:%(message)s',
                        level=logging.INFO)

    game_builder = GameBuilder()
    draw_scorecard = DrawScorecard()

    start_date = datetime(2018, 10, 5)
    for date in [start_date + timedelta(days=x) for x in range(0, 200)]:
        games = statsapi.schedule(
            start_date='%d/%d/%d' % (date.month, date.day, date.year))

        for game_dict in games:
            logging.info('Processing %d %s %s vs. %s', game_dict['game_id'],
                         game_dict['game_date'], game_dict['away_name'],
                         game_dict['home_name'])
            game = game_builder.build(game_dict['game_id'])
            drawing = draw_scorecard.draw(game)
            drawing.saveas('test.svg')

            #for inning in game:
            #    print(inning)
            #    for half in inning:
            #        print(half)
            #        for atbat in half:
            #            print(atbat)
            #            for runner in atbat.mid_pa_runners:
            #                print(runner, 'mid-pa')
            #            for runner in atbat.runners:
            #                print(runner)
            #input('Done')
