import unittest

from gd2score.pinch_runners import PinchRunnerFixer
from gd2score.models import AtBat, Action, HalfInning, Runner
from gd2score.parse_players import Player


class TestPinchRunnerFixer(unittest.TestCase):
    def setUp(self):
        self.fixer = PinchRunnerFixer()

        # gid_2018_03_29_phimlb_atlmlb_1 bot 8
        self.half_inning = HalfInning()
        action = Action(583, 'Passed Ball',
                        ('With Preston Tucker batting, passed ball by Andrew '
                         'Knapp, Freddie Freeman scores. Kurt Suzuki to 3rd. '
                         'Throwing error by catcher Andrew Knapp.'), 518692)
        self.half_inning.add_action(action)
        action = Action(585, 'Offensive Sub',
                        ('Offensive Substitution: Pinch-runner Peter Bourjos '
                         'replaces Kurt Suzuki.'), 488721)
        self.action = action
        self.half_inning.add_action(action)

        ab = AtBat(68, 593, 605512,
                   ('Preston Tucker singles on a line drive to center fielder '
                    'Odubel Herrera. Peter Bourjos scores.'), 'Single', 591693)
        self.ab = ab

        # mid_pa_runners
        ab.add_runner(Runner(id=435559, start=1, end=3, event_num=583))
        ab.add_runner(Runner(id=518692, start=2, end=4, event_num=583))

        # runners
        self.o_runner = Runner(id=435559, start=3, end=0, event_num=593)
        self.p_runner = Runner(id=488721, start=0, end=3, event_num=593)
        ab.add_runner(self.o_runner)
        ab.add_runner(self.p_runner)
        ab.add_runner(Runner(id=488721, start=3, end=4, event_num=593))
        ab.add_runner(Runner(id=605512, start=0, end=1, event_num=593))

        self.half_inning.add_atbat(ab)

        self.players = {
            488721: Player(488721, 'Peter', 'Bourjos'),
            435559: Player(435559, 'Kurt', 'Suzuki')
        }

    def test_pinch_runner_swap_removed(self):
        self.assertEqual(len(self.ab.mid_pa_runners), 2)
        self.assertEqual(len(self.ab.runners), 4)
        self.fixer.fix(self.ab, self.half_inning, self.players)
        self.assertEqual(len(self.ab.runners), 2)
        self.assertTrue(self.o_runner not in self.ab.runners)
        self.assertTrue(self.p_runner not in self.ab.runners)

    def test_get_swap_names(self):
        pr_name, or_name = self.fixer.get_swap_names(self.action)
        self.assertEqual(pr_name, 'Peter Bourjos')
        self.assertEqual(or_name, 'Kurt Suzuki')

    def test_swap_base_found(self):
        base = self.fixer.get_swap_base(self.ab, self.half_inning, 435559)
        self.assertEqual(base, 3)
