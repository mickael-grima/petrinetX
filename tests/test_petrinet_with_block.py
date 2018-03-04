import unittest

from src.petrinet import Petrinet


class TestBlockingPetrinet(unittest.TestCase):
    def test_blocking_rules_on_petrinet(self):
        adj_dict = dict(
            places=dict(
                place0=dict(tokens=1),
                place1=dict(tokens=1),
                place2=dict()
            ),
            transitions=dict(
                transition0=dict(
                    rules=dict(
                        FireInheritanceRule=dict(
                            args=("Transition::transition1",)
                        )
                    )
                ),
                transition1=dict(
                    rules=dict(
                        BlockingInheritanceRule=dict(
                            args=("Transition::transition2",)
                        )
                    )
                ),
                transition2=dict()
            ),
            graph=dict(
                place0=dict(
                    transition0=1
                ),
                place1=dict(
                    transition1=1
                ),
                place2=dict(
                    transition0=-1,
                    transition1=-1,
                    transition2=2
                )
            )
        )
        petrinet = Petrinet(adj_dict)
        petrinet.fire_queue.update()
        petrinet.fire_queue.optimize()

        self.assertEqual(
            map(lambda t: t.name, petrinet.fire_queue), ["transition0"])
        self.assertEqual(
            set(map(lambda p: p.name, list(petrinet.iter_token_places()))),
            {"place0", "place1"})

        # first fire
        petrinet.next()
        self.assertEqual(
            map(lambda t: t.name, petrinet.fire_queue), ["transition1"])
        self.assertEqual(
            set(map(lambda p: p.name, list(petrinet.iter_token_places()))),
            {"place1", "place2"})

        # second fire: transition2 is blocked and can't fire
        petrinet.next()
        self.assertTrue(petrinet.fire_queue.is_empty())
        self.assertTrue(petrinet.is_blocked())
        self.assertEqual(
            set(map(lambda p: p.name, list(petrinet.iter_token_places()))),
            {"place2"})


if __name__ == '__main__':
    unittest.main()
