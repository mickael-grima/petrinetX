# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

import unittest
from Petrinet import PetriNet
from Place import Place
from Transition import Transition
from Token import Token
from utils.builder import build_small_petrinet


class Test(unittest.TestCase):

    def setUp(self):
        self.pn = build_small_petrinet()
        self.places = sorted(self.pn.places.iterkeys(), key=lambda p: p.name)
        self.transitions = sorted(self.pn.transitions.iterkeys(), key=lambda t: t.name)

    def testStructure(self):
        self.assertEqual(self.pn.name, 'pn1', msg='False name')
        self.assertEqual(len(self.pn.places), 4, msg='Wrong number of places')
        self.assertEqual(len(self.pn.transitions), 5, msg='Wrong number of transitions')

        for place, rank in self.pn.places.iteritems():
            self.assertEqual(place.name, 'p%s' % rank)
        for transition, rank in self.pn.transitions.iteritems():
            self.assertEqual(transition.name, 't%s' % rank)

        for place in self.pn.places:
            self.assertIn(place, self.pn.inputs)
            self.assertIn(place, self.pn.outputs)
        for transition in self.pn.transitions:
            if transition.name != 't4':
                self.assertIn(transition, self.pn.downplaces)
            self.assertIn(transition, self.pn.upplaces)

    def testGetEnabledToken(self):
        tokens = [tok for tok in self.pn.getEnabledToken(self.places[0], self.transitions[0])]
        self.assertEqual(set(map(lambda tok: tok.name, tokens)), set(['token1', 'token2']))

    def testSimulation(self):
        self.pn.simulation(show=True)


if __name__ == '__main__':
    unittest.main()
