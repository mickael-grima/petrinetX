# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

from Petrinet import PetriNet
from Place import Place
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

    # ---------------------------------------------------------------
    # -------------------  BUILDING FUNCTIONS -----------------------
    # ---------------------------------------------------------------

    def addToken(self, place, *tokens):
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)
        if self.places.get(place) is None:
            self.logger.warning("Try to add a token to the inexistant place %s" % place.name)

        else:
            for token in tokens:
                try:
                    place.addToken(token)
                except:
                    continue

                if self.inputs.get(place) is not None:
                    for t in self.inputs[place].iterkeys():
                        token.addTransitionClock(t, t.getTransitionTime())
                        token.tclock[t] = token.transitionClocks[t]
                        token.addMinimumStartingTime(t, t.minimumStartingTime)
                if self.token.get(place) is None:
                    self.token.setdefault(place, 1)
                else:
                    self.token[place] += 1

    def savePlaces(self):
        for p in self.places.iterkeys():
            self.initialState.setdefault(p, [tok.copy() for tok in p.token])

    def setInitialState(self):
        self.savePlaces()
        self.saveTransitions()
        self.initialState.setdefault('initialClock', self.currentClock)

    def reinitialized(self):
        if len(self.initialState) != 0:
            for p in self.places.iterkeys():
                while p.token:
                    self.removeToken(p, p.token[0])
                for tok in self.initialState[p]:
                    self.addToken(p, tok)
            for t in self.transitions.iterkeys():
                t.tokenQueue = []
                t.tokenQueueAfterFire = []
                if self.initialState.get(t) is not None:
                    if self.initialState[t].get('tokenQueue'):
                        t.tokenQueue = self.initialState[t]['tokenQueue']
                    if self.initialState[t].get('tokenQueueAfterFire'):
                        t.tokenQueueAfterFire = self.initialState[t]['tokenQueueAfterFire']
            self.currentClock = self.initialState['initialClock']
            self.initialState = {}

    # ---------------------------------------------------------------
    # ----------------------  OTHER FUNCTIONS -----------------------
    # ---------------------------------------------------------------

    def optimalTimeEts(self, ets, duration=sys.maxint):
        """ Among the transitions in ``est``, compute the transition whose firing time is the minimal one.

            :param ets: set of enabled transitions
            :type ets: dict

            * options:
                * ``duration = sys.maxint``: if the minimal duration above is higher than ``duration``,
                                             then we return an empty list

            :returns: A list of objects :class:`Transition <petrinet_simulator.Transition>`
        """
        # compute the minimum of time for enabled transitions, and choose the transitions
        duration_, transitions, maxDuration = sys.maxint, [], {}

        for t, c in ets.iteritems():
            mx = 0.0

            # for each t we compute the maximum time of the places before
            if self.upplaces.get(t) is not None:
                for p, nb in self.upplaces[t].iteritems():
                    toks = self.getSortedNextFiredToken(p, t)
                    delta = toks[-1].minimumStartingTime.get(t, - sys.maxint - 1) - self.currentClock
                    mx = max(mx, delta, toks[-1].pclock) + toks[-1].tclock[t]

            # we save the duration before the firing of transition t
            maxDuration.setdefault(t, mx)

            # duration before the first firing
            if duration_ >= mx:
                duration_ = mx

        # we collect the transitions that can fire at the same minimal time duration
        for t, d in maxDuration.iteritems():
            if d <= duration and d == duration_:
                transitions.append(t)

        return transitions, duration_
