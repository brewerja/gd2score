import unittest

from gd2score.enhance import GameEnhancer, BaseNotFoundException
from gd2score.parse_players import Player


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
