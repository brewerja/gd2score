import re
from datetime import datetime, timedelta
import logging
import urllib.request

from bs4 import BeautifulSoup

from .driver import GameBuilder, GD2_URL, GID_REGEX
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


def get_games(year, month, day):
    games = {}
    for gid in list_game_ids(year, month, day):
        m = re.match(GID_REGEX, gid)
        if m:
            games[gid] = ('%s @ %s' %
                          (m.group('away').upper(),
                           m.group('home').upper()))
    return games


def parse_gid_for_date(gid):
    m = re.match(GID_REGEX, gid)
    if m:
        return int(m.group('year')), int(m.group('month')), int(m.group('day'))
    raise ValueError


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
