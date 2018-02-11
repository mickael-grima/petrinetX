import unittest

from src.petrinet import Petrinet
from src.nodes import Transition, Place
from src.tokens import Token


class TestPetrinet(unittest.TestCase):
    def test_petrinet(self):
        """
        2 fires petrinet
        """
        petrinet = Petrinet()

        transition1, transition2 = Transition(), Transition()
        place0, place1, place2 = Place(), Place(), Place()


if __name__ == "__main__":
    unittest.main()
