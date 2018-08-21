import shutil
import tempfile
import urllib.request
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from parse_game import GameParser
from parse_players import PlayersParser
from draw_scorecard import draw

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
    #with open('players.xml') as f:
    #    players = PlayersParser(f.read()).players
    #with open('inning_all.xml') as f:
    #    game = GameParser(f.read())
    #draw(game, players)

    # Parsed 8/11 - 8/13 successfully!

    start_date = datetime(2018, 7, 8)  # Started from 4/1
    for date in [start_date + timedelta(days=x) for x in range(0, 10)]:
        game_ids = list_game_ids(date.year, date.month, date.day)
        for game_id in game_ids:
            try:
                game_url = get_game_url(game_id)
                players = PlayersParser(get(game_url + 'players.xml')).players
                print(game_id)
                game = GameParser(get(game_url + 'inning/inning_all.xml'))
                draw(game, players)
            except urllib.error.HTTPError:
                print(game_id, '404')

# 8/11 BOS game 2: Jackie Bradley Jr. lines out sharply, pitcher Yefry Ramirez to third baseman
# Renato Nunez to first baseman Trey

# 8/12  'Cory Spangenberg hits a sacrifice bunt. Freddy Galvis scores.
# Christian Villanueva to 3rd. Cory Spangenberg to 2nd. Throwing error by
# pitcher Austin Davis.'
