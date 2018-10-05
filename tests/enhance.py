import unittest

from gd2score.enhance import GameEnhancer, BaseNotFoundException
from gd2score.parse_players import Player
from gd2score.models import AtBat, Runner


class TestGameEnhancer(unittest.TestCase):
    def setUp(self):
        self.enhancer = GameEnhancer()

    def test_find_base_where_out_was_made(self):
        last_name = 'Brewer'
        descriptions = [
            ('John Brewer out at 1st', 1),
            ('John Brewer doubled off 2nd', 2),
            ('John Brewer picked off and caught stealing 3rd', 3),
            ('John Brewer caught stealing home', 4),
            ('John Brewer was picked off 1st', 1),
            ('picks off John Brewer at 1st', 1),
            ('picks off John Brewer at 1st', 1),
        ]
        for (des, expected_base) in descriptions:
            base = self.enhancer.find_base_where_out_was_made(last_name, des)
            self.assertEqual(base, expected_base)

    def test_find_base_throws_exception_when_not_found(self):
        last_name = 'Brewer'
        des = 'This is just garbage that will not find a base'
        with self.assertRaises(BaseNotFoundException) as context:
            self.enhancer.find_base_where_out_was_made(last_name, des)
        self.assertTrue(last_name in str(context.exception))

    def test_set_runner_out_bases_easy(self):
        # All runners with end == 0 should be out in the easy case
        self.enhancer.players = {
            11111: Player(11111, 'Trea', 'Turner'),
            22222: Player(22222, 'Anthony', 'Rendon'),
            33333: Player(33333, 'Juan', 'Soto'),
            44444: Player(44444, 'Victor', 'Robles'),
        }
        des = ('lines into an unassisted triple play, pitcher really a quad'
               'Trea Turner out at 1st, Anthony Rendon out at 2nd, '
               'Juan Soto out at 3rd, Victor Robles out at home')
        ab = AtBat(1, 1, 12345, des, 'Triple Play', 54321)
        ab.add_runner(Runner(id=11111, start=0, end=0, event_num=1))
        ab.add_runner(Runner(22222, 1, 0, 1))
        ab.add_runner(Runner(33333, 2, 0, 1))
        ab.add_runner(Runner(44444, 2, 0, 1))
        self.enhancer.set_runner_out_bases(ab)

        self.assertEqual(sum([1 for r in ab.runners if r.out]), 4)
        self.assertEqual(list(range(1, 5)), [r.end for r in ab.runners])
