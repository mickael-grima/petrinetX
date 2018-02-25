import unittest

from src.petrinet import Petrinet
from src.nodes import Transition, Place
from src.tokens import Token


class TestPetrinet(unittest.TestCase):
    def test_build(self):
        """
        2 fires petrinet
        """
        # Dict containing transitions and places
        transition1, transition2 = Transition(), Transition()
        place0, place1, place2 = Place(), Place(), Place()
        adj_matrix = {
            "graph": {
                place0: {transition1: 1},
                place1: {transition1: -1, transition2: 2},
                place2: {transition2: -1}
            }
        }

        petrinet = Petrinet(adj_matrix)

        # test graph structure
        self.assertTrue(petrinet.has_node(place0))
        self.assertTrue(petrinet.has_node(place1))
        self.assertTrue(petrinet.has_node(place2))
        self.assertTrue(petrinet.has_node(transition1))
        self.assertTrue(petrinet.has_node(transition2))
        self.assertTrue(petrinet.has_edge(place0, transition1))
        self.assertTrue(petrinet.has_edge(transition1, place1))
        self.assertTrue(petrinet.has_edge(place1, transition2))
        self.assertTrue(petrinet.has_edge(transition2, place2))
        self.assertFalse(petrinet.has_edge(transition1, place0))

    def test_flow_step_by_step(self):
        transition1, transition2 = Transition(), Transition()
        place0, place1, place2 = Place(), Place(), Place()
        place0.add_tokens(Token(), Token())
        adj_matrix = {
            "graph": {
                place0: {transition1: 1},
                place1: {transition1: -1, transition2: 2},
                place2: {transition2: -1}
            }
        }

        # test fire_queue
        petrinet = Petrinet(adj_matrix)
        self.assertIn(transition1, petrinet.fire_queue)
        self.assertIn(transition2, petrinet.fire_queue)

        # test fire_queue.optimize
        petrinet.fire_queue.update()
        petrinet.fire_queue.optimize()
        self.assertIn(transition1, petrinet.fire_queue)
        self.assertNotIn(transition2, petrinet.fire_queue)

        # test fire
        transition = petrinet.fire_queue.next()
        transition.fire()
        self.assertFalse(place0.has_n_tokens(2))
        self.assertTrue(place0.has_n_tokens(1))
        self.assertTrue(place1.has_n_tokens(1))
        self.assertFalse(place1.has_n_tokens(2))

        # test update fire_queue
        petrinet.fire_queue.update(transition)
        self.assertIn(transition1, petrinet.fire_queue)
        self.assertNotIn(transition2, petrinet.fire_queue)
        petrinet.fire_queue.optimize()
        transition = petrinet.fire_queue.next()
        transition.fire()
        self.assertFalse(place0.has_n_tokens(1))
        self.assertTrue(place1.has_n_tokens(2))

        # fire number 3
        petrinet.fire_queue.update(transition)
        self.assertIn(transition2, petrinet.fire_queue)
        self.assertNotIn(transition1, petrinet.fire_queue)
        petrinet.fire_queue.optimize()
        transition = petrinet.fire_queue.next()
        transition.fire()
        self.assertFalse(place0.has_n_tokens(1))
        self.assertFalse(place1.has_n_tokens(1))
        self.assertTrue(place2.has_n_tokens(1))

        # no fire anymore
        petrinet.fire_queue.update(transition)
        self.assertNotIn(transition1, petrinet.fire_queue)
        self.assertNotIn(transition2, petrinet.fire_queue)
        petrinet.fire_queue.optimize()
        self.assertTrue(petrinet.is_blocked())

    def test_simulate_method(self):
        transition1, transition2 = Transition(), Transition()
        place0, place1, place2 = Place(), Place(), Place()
        place0.add_tokens(Token(), Token())
        adj_matrix = {
            "graph": {
                place0: {transition1: 1},
                place1: {transition1: -1, transition2: 2},
                place2: {transition2: -1}
            }
        }

        petrinet = Petrinet(adj_matrix)
        petrinet.simulate()

        self.assertFalse(place0.has_n_tokens(1))
        self.assertFalse(place1.has_n_tokens(1))
        self.assertTrue(place2.has_n_tokens(1))
        self.assertTrue(petrinet.is_blocked())
        self.assertRaises(StopIteration, petrinet.next)


if __name__ == "__main__":
    unittest.main()
