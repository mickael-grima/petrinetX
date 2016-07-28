# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

import unittest
from Token import Token
from utils.builder import (
    build_small_petrinet,
    build_chain_petrinet,
    build_simple_conflicts,
    build_parallel_chain_petrinet
)


class Test(unittest.TestCase):

    def setUp(self):
        self.pn = build_small_petrinet()
        self.pn.addToken(self.pn.getPlace('p0'), Token(name='token0'), Token(name='token1'))
        self.pn.addToken(self.pn.getPlace('p2'), Token(name='token2'))

        self.chain_pn = build_chain_petrinet()
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
        self.assertEqual(set(map(lambda tok: tok.name, tokens)), set(['token0', 'token1']))

    def testSimulationChainPetrinet(self):
        """ Run a simulation on chain_pn and check if each step are right
            Test a simple petrinet, without additional properties
        """
        pn = build_chain_petrinet()
        pn.addToken(pn.getPlace('p0'), Token(name='tok0'))

        ets = pn.enabledTransitionsSet()
        for i in range(len(pn.places)):
            for place, rank in pn.places.iteritems():
                if rank == i:
                    self.assertIn('tok0', map(lambda tok: tok.name, place.token))
                else:
                    self.assertFalse(place.token)
            self.assertIn('t%s' % i, map(lambda tr: tr.name, ets.iterkeys()))
            pn.oneFireSimulation(ets)

    def testSimulationSimpleConflictsPetrinet(self):
        """ Test token priority: on one place has a token two transition choices. We impose one choice
        """
        pn = build_simple_conflicts()
        tok0 = Token(name='tok')
        p0 = pn.getPlace('p0')
        tok0.addPriority(p0, pn.getTransition('t0'))
        pn.addToken(p0, tok0)

        pn.simulation(show=False)
        self.assertIn('tok', map(lambda tok: tok.name, pn.getPlace('p1').token))
        self.assertFalse(pn.getPlace('p0').token)
        self.assertFalse(pn.getPlace('p2').token)

    def testSimulationParallelChainPetrinet(self):
        """ Test the fireheritance: a token could wait that another token hs been fired by a transition
            on a given place to have the right to be fired
        """
        # Without fireHeritance
        pn = build_parallel_chain_petrinet(size=1, branchs=2)
        tok0 = Token(name='tok0')
        tok1 = Token(name='tok1', fire=False)
        pn.addToken(pn.getPlace('p_0_0'), tok0)
        pn.addToken(pn.getPlace('p_1_0'), tok1)

        pn.simulation(show=False)

        self.assertIn('tok1', map(lambda tok: tok.name, pn.getPlace('p_1_0').token))

        # With fireHeritance
        pn = build_parallel_chain_petrinet(size=1, branchs=2)
        tok0 = Token(name='tok0')
        tok1 = Token(name='tok1', fire=False)
        tok0.addFireHeritance('tok1', pn.getPlace('p_1_0'), pn.getTransition('t_0_0'))
        pn.addToken(pn.getPlace('p_0_0'), tok0)
        pn.addToken(pn.getPlace('p_1_0'), tok1)

        ets = pn.enabledTransitionsSet()
        self.assertIn('tok0', map(lambda tok: tok.name, pn.getPlace('p_0_0').token))
        self.assertIn('tok1', map(lambda tok: tok.name, pn.getPlace('p_1_0').token))
        self.assertFalse(tok1.fire)

        pn.oneFireSimulation(ets)
        self.assertFalse(pn.getPlace('p_0_0').token)
        self.assertIn('tok1', map(lambda tok: tok.name, pn.getPlace('p_1_0').token))
        self.assertTrue(tok1.fire)

        pn.oneFireSimulation(ets)
        self.assertFalse(pn.getPlace('p_0_0').token)
        self.assertFalse(pn.getPlace('p_1_0').token)


if __name__ == '__main__':
    unittest.main()
