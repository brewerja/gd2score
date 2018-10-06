import unittest

from gd2score.enhance import GameEnhancer
from gd2score.models import Action, AtBat, Runner, Player


class TestFixMidPaRunners(unittest.TestCase):
    def setUp(self):
        self.enhancer = GameEnhancer()
        self.enhancer.players = {605141: Player(605141, 'Mookie', 'Betts')}

        action = Action(418, 'Runner Out',
                        ('Mookie Betts out at 1st, catcher Wilson Ramos to '
                         'first baseman C. J. Cron.'), 605141)
        self.ab = AtBat(55, 423, 434670,
                        'Hanley Ramirez walks.', 'Walk', 643493)
        self.ab.add_runner(Runner(605141, 1, 0, 418))
        self.ab.add_runner(Runner(434670, 0, 1, 423))
        self.ab.add_action(action)

    def test_fix_mid_pa_runners(self):
        self.enhancer.fix_mid_pa_runners(self.ab)
        runner_out = self.ab.mid_pa_runners[0]
        self.assertEqual(runner_out.end, 1)
        self.assertTrue(runner_out.out)
