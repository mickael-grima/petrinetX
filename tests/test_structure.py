import unittest

from src.nodes import Transition, Place
from src.petrinet import Petrinet
from src.rules import TimePlaceRule, DefaultPlaceRule, TimeTransitionRule, DefaultTransitionRule


class StructureTest(unittest.TestCase):
    def assert_structure(self, petrinet, nb_places=0, nb_transitions=0,
                         nb_edges=0):
        self.assertEqual(petrinet.number_of_nodes(), nb_transitions + nb_places)
        self.assertEqual(petrinet.number_of_edges(), nb_edges)

        places, transitions = 0, 0
        for node in petrinet.nodes():
            if isinstance(node, Place):
                places += 1
                self.assertIn(
                    petrinet.DEFAULT_PLACE_RULE,
                    map(lambda r: r.__class__, node.rules))
            elif isinstance(node, Transition):
                transitions += 1
                self.assertIn(
                    petrinet.DEFAULT_TRANSITION_RULE,
                    map(lambda r: r.__class__, node.rules))
            else:
                raise TypeError("node of type %s found" % type(node))
        self.assertEqual(places, nb_places)
        self.assertEqual(transitions, nb_transitions)

    def test_adjacent_matrix(self):
        adj_matrix = [[1, 0, 0], [2, 0, 0], [0, -1, 1], [0, 0, -3]]
        petrinet = Petrinet(adj_matrix)

        self.assert_structure(petrinet, 4, 3, 5)

    def test_adjacent_dict(self):
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
        self.assert_structure(petrinet, 3, 2, 4)

        adj_matrix = {
            "graph": {
                "place0": {"transition1": 1},
                place1: {"transition1": -1, transition2: 2},
                "place2": {transition2: -1}
            }
        }
        petrinet = Petrinet(adj_matrix)
        self.assert_structure(petrinet, 3, 2, 4)

    def test_adjacent_dict_with_properties(self):
        adj_matrix = dict(
            places=dict(
                place0=dict(
                    rules=dict(
                        TimePlaceRule=dict(
                            waiting_time=2,
                            global_clock=0
                        )
                    ),
                    tokens=1
                ),
                place1=dict(
                    rules=dict(
                        DefaultPlaceRule=dict()
                    ),
                    tokens=2
                ),
                place3=dict(
                    rules=dict(
                        default=dict()
                    )
                )
            ),
            transitions=dict(
                transition0=dict(
                    rules=dict(
                        TimeTransitionRule=dict()
                    )
                )
            ),
            graph=dict(
                place0=dict(
                    transition0=1,
                ),
                place1=dict(
                    transition0=2,
                ),
                place2=dict(
                    transition0=-1,
                    transition1=1
                ),
                place3=dict(
                    transition1=-1,
                )
            )
        )
        petrinet = Petrinet(adj_matrix)

        self.assert_structure(petrinet, 4, 2, 5)

        place0 = petrinet.iter_places_by_name("place0").next()
        self.assertIn(
            TimePlaceRule.__name__,
            map(lambda r: r.__class__.__name__, place0.rules))
        self.assertIn(
            DefaultPlaceRule.__name__,
            map(lambda r: r.__class__.__name__, place0.rules))
        self.assertEqual(len(place0.rules), 2)
        self.assertTrue(place0.has_n_tokens(1))
        self.assertFalse(place0.has_n_tokens(2))


if __name__ == '__main__':
    unittest.main()
