import shutil
import tempfile
import urllib.request
from datetime import datetime, timedelta
import logging

from bs4 import BeautifulSoup

from parse_game import GameParser
from parse_players import PlayersParser
from draw_scorecard import draw
from enhance import GameEnhancer

GD2_URL = 'https://gd2.mlb.com/components/game/mlb'


def get(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def get_game_url(gid):
    p = gid.split('_')
    return ('%s/year_%04d/month_%02d/day_%02d/%s/' %
            (GD2_URL, int(p[1]), int(p[2]), int(p[3]), gid))


def list_game_ids(year, month, day):
    html = get('%s/year_%04d/month_%02d/day_%02d' %
               (GD2_URL, year, month, day))
    soup = BeautifulSoup(html, 'html.parser')
    links = [a.get('href').split('/')[1] for a in soup.find_all('a')]
    return [l for l in links if l.startswith('gid')]


def get_todays_game_ids():
    d = datetime.now()
    return list_game_ids(d.year, d.month, d.day)


if __name__ == '__main__':
#    with open('players.xml') as f:
#        players = PlayersParser(f.read()).players
#    with open('inning_all.xml') as f:
#        game = GameParser(f.read())
#    draw(game, players)

    logging.basicConfig(format='%(levelname)s:%(message)s',
                        level=logging.WARNING)

    start_date = datetime(2014, 4, 1)
    for date in [start_date + timedelta(days=x) for x in range(0, 200)]:
        game_ids = list_game_ids(date.year, date.month, date.day)
        for game_id in game_ids:
            try:
                game_url = get_game_url(game_id)
                players = PlayersParser(get(game_url + 'players.xml')).players
                print(game_id)
                game = GameParser(get(game_url + 'inning/inning_all.xml'))
                game = GameEnhancer(game, players)
                draw(game, players)
                break
            except urllib.error.HTTPError:
                print(game_id, '404')
