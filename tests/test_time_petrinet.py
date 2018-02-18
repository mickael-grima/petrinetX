import unittest

from src.nodes import Transition, Place
from src.tokens import Token
from src.rules import TimeTransitionRule, TimePlaceRule
from src.fire_queues import TimeFireQueue


class TimePetrinetTest(unittest.TestCase):
    def test_time_rule(self):
        transition = Transition()
        place0, place1, place2 = Place(), Place(), Place()
        transition.add_rule(TimeTransitionRule)
        place0.add_rule(TimePlaceRule, waiting_time=2, global_clock=10)
        place1.add_rule(TimePlaceRule, waiting_time=1, global_clock=10)
        place2.add_rule(TimePlaceRule, waiting_time=2, global_clock=10)

        transition.add_down_place(place0, 1)
        transition.add_down_place(place1, 2)
        transition.add_up_place(place2, 1)

        place0.add_tokens(Token(clock=1))
        place1.add_tokens(Token(clock=2))
        place1.add_tokens(Token(clock=5))

        self.assertTrue(transition.is_fireable())
        self.assertEqual(
            place0.get_rule(TimePlaceRule.__name__).get_value(0), 9)
        self.assertEqual(
            place1.get_rule(TimePlaceRule.__name__).get_value(0), 8)
        self.assertEqual(
            place1.get_rule(TimePlaceRule.__name__).get_value(1), 5)
        self.assertEqual(
            transition.get_rule(TimeTransitionRule.__name__).get_value(), 9)

        transition.fire(12)
        self.assertEqual(
            place0.get_rule(TimePlaceRule.__name__).global_clock, 12)
        self.assertEqual(
            place1.get_rule(TimePlaceRule.__name__).global_clock, 12)

    def test_time_fire_queue(self):
        # Create objects
        transition0, transition1 = Transition(), Transition()
        place0, place1, place2, place3 = Place(), Place(), Place(), Place()
        transition0.add_rule(TimeTransitionRule)
        transition1.add_rule(TimeTransitionRule)
        place0.add_rule(TimePlaceRule, waiting_time=2, global_clock=0)
        place1.add_rule(TimePlaceRule, waiting_time=1, global_clock=0)
        place2.add_rule(TimePlaceRule, waiting_time=3, global_clock=0)
        place3.add_rule(TimePlaceRule, waiting_time=2, global_clock=0)

        transition0.add_down_place(place0, 1)
        transition0.add_down_place(place1, 2)
        transition0.add_up_place(place2, 1)
        transition1.add_down_place(place2, 1)
        transition1.add_up_place(place3, 1)

        place0.add_up_transition(transition0)
        place1.add_up_transition(transition0)
        place2.add_down_transition(transition0)
        place2.add_up_transition(transition1)
        place3.add_down_transition(transition0)

        place0.add_tokens(Token(clock=0))
        place1.add_tokens(Token(clock=0))
        place1.add_tokens(Token(clock=0))

        fire_queue = TimeFireQueue()
        fire_queue.insert_transition(transition0)
        fire_queue.insert_transition(transition1)

        # Update the fire queue
        fire_queue.update()
        self.assertIn(transition0, fire_queue)
        self.assertNotIn(transition1, fire_queue)

        # optimize
        fire_queue.optimize()
        self.assertIn(transition0, fire_queue)
        self.assertNotIn(transition1, fire_queue)
        self.assertEqual(fire_queue.optimal_value, 2)

        # fire the first transition
        transition = fire_queue.pop_and_fire()
        fire_queue.update(transition)
        self.assertEqual(
            place0.get_rule(TimePlaceRule.__name__).global_clock, 2)
        self.assertEqual(
            place1.get_rule(TimePlaceRule.__name__).global_clock, 2)
        self.assertEqual(
            place2.get_rule(TimePlaceRule.__name__).global_clock, 2)
        self.assertFalse(place0.has_n_tokens(1))
        self.assertFalse(place1.has_n_tokens(1))
        self.assertTrue(place2.has_n_tokens(1))
        for token in place2.iter_tokens():
            self.assertTrue(hasattr(token, "clock"))
            self.assertEqual(token.clock, 2)
        self.assertIn(transition1, fire_queue)
        self.assertNotIn(transition0, fire_queue)

        # second optimization
        fire_queue.optimize()
        self.assertIn(transition1, fire_queue)
        self.assertNotIn(transition0, fire_queue)
        self.assertEqual(fire_queue.optimal_value, 3)

        # fire the first transition
        transition = fire_queue.pop_and_fire()
        fire_queue.update(transition)
        self.assertEqual(
            place2.get_rule(TimePlaceRule.__name__).global_clock, 5)
        self.assertEqual(
            place3.get_rule(TimePlaceRule.__name__).global_clock, 5)
        self.assertFalse(place2.has_n_tokens(1))
        self.assertTrue(place3.has_n_tokens(1))
        for token in place3.iter_tokens():
            self.assertTrue(hasattr(token, "clock"))
            self.assertEqual(token.clock, 5)
        self.assertNotIn(transition1, fire_queue)
        self.assertNotIn(transition0, fire_queue)

    def test_time_petrinet(self):
        pass


if __name__ == "__main__":
    unittest.main()
