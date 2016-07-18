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


class Test(unittest.TestCase):

    def setUp(self):
        pl0 = Place(name='p0')
        pl1 = Place(name='p1')
        pl2 = Place(name='p2')
        pl3 = Place(name='p3')
        places = [pl0, pl1, pl2, pl3]

        tr0 = Transition(name='t0')
        tr1 = Transition(name='t1')
        tr2 = Transition(name='t2')
        tr3 = Transition(name='t3')
        tr4 = Transition(name='t4')
        transitions = [tr0, tr1, tr2, tr3, tr4]

        inputs = [[1, 1, 0, 0, 0],
                  [0, 0, 1, 1, 0],
                  [0, 0, 0, 0, 1],
                  [0, 0, 0, 0, 1]]

        outputs = [[1, 0, 0, 0, 0],
                   [0, 2, 0, 0, 0],
                   [0, 0, 1, 0, 0],
                   [0, 0, 0, 1, 0]]

        tok = Token()
        tokens = {pl0: [tok.copy(), tok.copy()], pl2: [tok.copy()]}

        self.pn = PetriNet('pn1')

        self.pn.buildPetriNet(places, transitions, inputs, outputs, tokens)

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


if __name__ == '__main__':
    unittest.main()
