import shutil
import tempfile
import urllib.request
from datetime import datetime

from bs4 import BeautifulSoup

from parse_game import GameParser
from parse_players import PlayersParser

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
    game_ids = list_game_ids(2018, 8, 11)
    event_types = set()
    for game_id in game_ids:
        game_url = get_game_url(game_id)
        players = PlayersParser(get(game_url + 'players.xml')).players
        for p in players:
            print('%d %s. %s' % (p.id, p.first[0], p.last))
        g = GameParser(get(game_url + 'inning/inning_all.xml'))
        event_types = event_types.union(g.event_types)
    print(event_types)
