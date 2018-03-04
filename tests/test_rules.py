import unittest

from src.nodes import Transition
from src.rules import BlockedFireRule, FireInheritanceRule, \
    BlockingInheritanceRule


class TestRules(unittest.TestCase):
    def test_blocking_rules(self):
        transition0 = Transition()
        transition1 = Transition()
        transition2 = Transition()

        for transition in [transition0, transition1, transition2]:
            self.assertTrue(transition.is_fireable())

        transition0.add_rule(BlockedFireRule)
        transition0.add_rule(BlockingInheritanceRule, transition2)
        transition1.add_rule(FireInheritanceRule, transition0)
        transition2.add_rule(BlockedFireRule)

        self.assertFalse(transition0.is_fireable())
        self.assertTrue(transition1.is_fireable())
        self.assertTrue(transition2.is_fireable())

        transition1.fire()
        for transition in [transition0, transition1, transition2]:
            self.assertTrue(transition.is_fireable())

        transition2.fire()
        for transition in [transition0, transition1, transition2]:
            self.assertTrue(transition.is_fireable())

        transition0.fire()
        self.assertFalse(transition2.is_fireable())
        self.assertTrue(transition1.is_fireable())
        self.assertTrue(transition0.is_fireable())


if __name__ == '__main__':
    unittest.main()
