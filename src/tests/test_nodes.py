import unittest

from src.nodes import Transition, Place
from src.tokens import Token
from src.rules import DefaultTransitionRule, DefaultPlaceRule


class TestNodes(unittest.TestCase):
    def test_nodes_iter_functions(self):
        """
        Test transition and place creation, down and up nodes, and iteration
        methods
        """
        transition = Transition()
        place0, place1, place2 = Place(), Place(), Place()

        transition.add_down_place(place0)
        transition.add_down_place(place1, flow=2)
        transition.add_up_place(place2)

        # Assert that any place has no tokens
        self.assertFalse(place0.has_n_tokens(flow=1))
        self.assertFalse(place1.has_n_tokens(flow=2))
        place0.add_tokens(Token())
        self.assertTrue(place0.has_n_tokens(flow=1))
        self.assertFalse(place0.has_n_tokens(flow=2))
        place0.add_tokens(Token())
        self.assertTrue(place0.has_n_tokens(flow=1))
        self.assertTrue(place0.has_n_tokens(flow=2))

        # Test pop tokens
        tokens = place0.pop_n_tokens(flow=2)
        self.assertEqual(len(tokens), 2)
        self.assertFalse(place0.has_n_tokens())
        self.assertFalse(place1.pop_n_tokens(flow=4))

        # Test if iteration methods work
        self.assertIn(place0, set(transition.iter_down_places()))
        self.assertIn(place1, set(transition.iter_down_places()))
        self.assertEqual(2, transition.get_place_flow(place1))
        self.assertEqual(len(list(transition.iter_down_places())), 2)
        self.assertEqual(list(transition.iter_up_places()), [place2])
        self.assertEqual(
            {place0, place1, place2}, set(transition.iter_places()))

    def test_default_transition_rule(self):
        # Test the default rule
        transition = Transition()
        place0, place1, place2 = Place(), Place(), Place()

        transition.add_down_place(place0)
        transition.add_down_place(place1, flow=2)
        transition.add_up_place(place2)
        # add rules
        transition.add_rule(DefaultTransitionRule)
        place0.add_rule(DefaultPlaceRule)
        place1.add_rule(DefaultPlaceRule)
        place2.add_rule(DefaultPlaceRule)

        # No rule so transition is not fire-able
        self.assertFalse(transition.is_fireable())

        place0.add_tokens(Token())
        place1.add_tokens(Token())

        # place1 still doesn't have enough tokens
        self.assertFalse(transition.is_fireable())

        # add the last missing token
        place1.add_tokens(Token())
        self.assertTrue(transition.is_fireable())

        # even if some places have too many tokens
        place0.add_tokens(Token())
        self.assertTrue(transition.is_fireable())

        # fire action
        transition.fire()
        self.assertFalse(place1.has_n_tokens())
        self.assertFalse(place0.has_n_tokens(2))
        self.assertTrue(place0.has_n_tokens())  # still one token remaining
        self.assertTrue(place2.has_n_tokens())  # one more token
        self.assertFalse(place2.has_n_tokens(2))  # but only one

        # so transition is not fire-able anymore
        self.assertFalse(transition.is_fireable())


if __name__ == '__main__':
    unittest.main()
