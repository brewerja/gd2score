from datetime import datetime, timedelta
import logging
import urllib.request

from bs4 import BeautifulSoup

from .driver import GameBuilder, GD2_URL
from .draw_scorecard import DrawScorecard
from .parse_game import IncompleteGameException


def get(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def list_game_ids(year, month, day):
    html = get('%s/year_%04d/month_%02d/day_%02d' %
               (GD2_URL, year, month, day))
    soup = BeautifulSoup(html, 'html.parser')
    links = [a.get('href').split('/')[1] for a in soup.find_all('a')]
    return [l for l in links if l.startswith('gid')]


if __name__ == '__main__':
    logging.basicConfig(  # filename='parsing.log',
                        format='%(levelname)s:%(message)s',
                        level=logging.DEBUG)

    game_builder = GameBuilder()
    draw_scorecard = DrawScorecard()
    start_date = datetime(2016, 5, 20)
    for date in [start_date + timedelta(days=x) for x in range(0, 200)]:
        game_ids = list_game_ids(date.year, date.month, date.day)
        for game_id in game_ids:
            if game_id in ['gid_2014_04_16_atlmlb_phimlb_1',
                           'gid_2014_05_23_arimlb_nynmlb_1',
                           'gid_2014_08_12_arimlb_clemlb_1']:
                continue
            try:
                logging.info('Processing %s', game_id)
                game = game_builder.build(game_id)
                drawing = draw_scorecard.draw(game)
                drawing.saveas('test.svg')

                input(game_id)
            except urllib.error.HTTPError:
                logging.info('Not found: %s', game_id)
            except IncompleteGameException:
                logging.info('Incomplete game: %s', game_id)
