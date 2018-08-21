import unittest

from parse_players import Player, PlayersParser


class PlayerTest(unittest.TestCase):
    def test_simple_first_last(self):
        p = Player(2, 'Max', 'Scherzer')
        self.assertEqual(p.__str__(), 'M. Scherzer')

    def test_abbrev_name(self):
        p = Player(1, 'A. J.', 'Cole')
        self.assertEqual(p.__str__(), 'A.J. Cole')


class PlayersParserTest(unittest.TestCase):
    def setUp(self):
        with open('players.xml', 'rb') as f:
            self.xml = f.read()
        self.pp = PlayersParser(self.xml)

    def test_number_of_players(self):
        self.assertEqual(len(self.pp.players), 59)

    def test_players_from_each_team(self):
        self.assertEqual(self.pp.players.get(519306).__str__(), 'S. Souza Jr.')
        self.assertEqual(self.pp.players.get(572041).__str__(), 'A.J. Pollock')
        self.assertEqual(self.pp.players.get(547179).__str__(), 'M. Lorenzen')


if __name__ == '__main__':
    unittest.main()
