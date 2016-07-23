# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

from Petrinet import PetriNet
import logging


class TimePetriNet(PetriNet):
    """This class herites from :class:`PetriNet <petrinet_simulator.PetriNet>`.

    The time is added, and simulations are also possible
    """
    # fields used in this class
    #
    # tclock -> dictionnary that repertory each clock whom the key is the associated transition
    # currentClock -> The current time
    #
    # for places: each token have to stay time on each place. A fire doesn't reinitialize the clock of a place
    # for transitions: if a transition fire, it reinitializes its own clock, but not the others.

    # ---------------------------------------------------------------
    # -------------------  CONSTRUCTOR   ----------------------------
    # ---------------------------------------------------------------

    def __init__(self, name=None, logger=logging, startDate=None, currentClock=0.0):
        PetriNet.__init__(self, name)
        self.currentClock = currentClock
        self.startDate = startDate

    def copy(self):
        pn = TimePetriNet(self.name)
        copy = {}
        for p in self.places.iterkeys():
            copy.setdefault(p, p.copy())
            pn.addPlace(copy[p])

        for t in self.transitions.iterkeys():
            copy.setdefault(t, t.copy())
            pn.addTransition(copy[t])

        # Make a copy of tokens
        for p in pn.places.iterkeys():
            for tok in p.token:
                tok.placeClocks = {copy[pl]: cl for pl, cl in tok.placeClocks.iteritems()}
                tok.transitionClocks = {copy[tr]: cl for tr, cl in tok.transitionClocks.iteritems()}
                tok.tclock = {copy[tr]: cl for tr, cl in tok.tclock.iteritems()}
                tok.priority = {
                    copy[pl]: {
                        'priority': [copy[tr] for tr in attr['priority']],
                        'pref': attr['pref']
                    } for pl, attr in tok.priority.iteritems()
                }
                tok.priorityAfterFire = {
                    copy[tr]: {
                        loc: {
                            copy[pl]: {
                                'priority': [copy[t] for t in attr['priority']],
                                'pref': attr['pref']
                            } for pl, attr in prt.iteritems()
                        } for loc, prt in dct.iteritems()
                    } for tr, dct in tok.priorityAfterFire.iteritems()
                }
                tok.fireHeritance = {
                    copy[tr]: {
                        copy[pl]: [tok for tokName in toks]
                        for pl, toks in dct.iteritems()
                    } for tr, dct in tok.fireHeritance.iteritems()
                }

        # Make a copy of transitions
        for t, c in pn.transitions.iteritems():
            t.tokenQueueAfterFire = [
                {
                    tkns: {
                        copy[tr]: {
                            'tokenQueue': [[tn for tn in tns] for tns in attr['tokenQueue']],
                            'place_presence': attr['place_presence'],
                            'nb_tok': attr['nb_tok']
                        } for tr, attr in dc.iteritems()
                    } for tkns, dc in dct.iteritems()
                } for dct in t.tokenQueueAfterFire
            ]

        for p, dct in self.inputs.iteritems():
            for t, n in dct.iteritems():
                pn.addInput(copy[p], copy[t], n)
        for p, dct in self.outputs.iteritems():
            for t, n in dct.iteritems():
                pn.addOutput(copy[p], copy[t], n)
        for p, n in self.token.iteritems():
            pn.token.setdefault(copy[p], n)

        pn.currentClock = self.currentClock
        pn.startDate = self.startDate

        return pn
