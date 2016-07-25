# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

from Petrinet import PetriNet
from Place import Place
from TimeToken import TimeToken
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

    def __getMinimumFiringTime(self, transition):
        mx = 0.0

        # for each t we compute the maximum time of the places before
        if self.upplaces.get(transition) is not None:
            for p, nb in self.upplaces[transition].iteritems():
                toks = self.getSortedNextFiredToken(p, transition)
                delta = toks[-1].minimumStartingTime.get(transition, - sys.maxint - 1) - self.currentClock
                mx = max(mx, delta, toks[-1].pclock) + toks[-1].tclock[transition]

        return mx

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
            mx = self.__getMinimumFiringTime(t)

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

    def __adapteClocks(self, transition, duration):
        for p in self.places.iterkeys():
            for tok in p.token:
                dur = max(0.0, duration - tok.pclock)
                tok.pclock = max(0.0, tok.pclock - duration)

                for t in (self.inputs.get(p) or {}).iterkeys():
                    delta = tok.minimumStartingTime.get(t, - sys.maxint - 1) - (self.currentClock + duration)
                    tok.tclock[t] = max(0.0, tok.tclock[t] - max(0.0, dur - max(0.0, delta)))

        for p in self.upplaces.get(transition, {}).iterkeys():
            for tok in p.token:
                tok.addTransitionClock(transition, transition.getTransitionTime())
                tok.tclock[transition] = tok.transitionClocks[transition]

    def __getTokenAfterFire(self, transition, ets, tok_save):
        tok = TimeToken()

        # add a name and first priorities to tok
        tok.__addFirstProperties(tok_save)

        # add clocks properties
        tok.__addClocksProperties(tok_save)

        # update advanced properties
        self.__updateAdvancedProperties(tok, transition, tok_save, ets)

        return tok

    def __adaptePetriNet(self, transition, duration, ets):
        fired_tokens = self.__fireToken(transition, ets)

        # We adapte the tokenQueue of targeted transitions and of transition
        self.__updateTokenQueue(transition, fired_tokens)

        # Adapte every place clocks
        self.__updateClocks(transition, duration)

        # create the token after the fire
        token = self.__getTokenAfterFire(transition, ets, fired_tokens)

        # Update the places and ets after the firing
        self.__updateAfterFiring(transition, token, ets)

    # ---------------------------------------------------------------
    # ----------------------  DYNAMIC FUNCTIONS ---------------------
    # ---------------------------------------------------------------

    def computeFiringTransition(self, ets, duration=sys.maxint):
        if not ets:
            return None, 0.0

        # compute the enabled transitions with minimal firing time
        transitions, duration_ = self.optimalTimeEts(ets, duration)

        return self.mostPriorityTransition(*transitions), duration_

    def fire(self, transition, ets, duration=0.0):
        """ Execute the firing of ``transition``, adapte ``ets`` and all places and tokens in the PetriNet

            :param transition: transition that fired
            :type transition: :class:`Transition <petrinet_simulator.Transition>`
            :param ets: set of enabled transitions
            :type ets: dict

            .. Warning:: ``ets`` must contain only enable transitions, otherwise an Error can be raised
        """
        # adapte the places
        self.__adaptePetriNet(transition, duration, ets)

    def oneFireSimulation(self, ets, duration=sys.maxint):
        """ Compute the next firing transition and execute the firing: the two methods called are
            :func:`computeFiringTransition <petrinet_simulator.PetriNet.computeFiringTransition>` and
            :func:`fire <petrinet_simulator.PetriNet.fire>`

            :param ets: set of enabled transitions
            :type ets: dict

            :returns: an object of class :class:`Transition <petrinet_simulator.Transition>`
        """
        # compute the minimum of time for enabled transitions, and choose the transition
        transition, duration_ = self.computeFiringTransition(ets, duration)

        if transition is None:
            return duration_, None

        # fire and adapte each clocks
        self.fire(transition, ets, duration_)

        # we return the new token and the duration
        return duration_, transition

    def simulation(self, show=True, step=None, niter=float('nan')):
        """ Execute the simulation of the PetriNet. It invoques in a loop the method
            :func:`oneFireSimulation <petrinet_simulator.PetriNet.oneFireSimulation>`

            * options:

                * ``show = True``: if True, informations about firing transitions and currentclock are printed
                * ``step = None``: If a value is given, at each step we increase the currentclock of step,
                                   and we try to fire a transition. If it's None, we compute the next firing transition
                                   and then we increase the currentclock of the necessary amont of time
                * ``niter = nan``: If a value is done, we do only ``niter`` iterations, if nan we iterate until
                                   there are no enabled transitions anymore
        """
        if not isinstance(show, bool):
            raise TypeError('Boolean expected, got a %s instead' % show.__class__.__name__)
        if not step and not isinstance(step, int) and not isinstance(step, long) and not isinstance(step, float):
            raise TypeError('Numaric value expected, got a %s instead' % step.__class__.__name__)

        if show:
            print 'beginning of the simulation'
            print 'currentTime : %s' % self.currentClock
            print ''

        if self.initialState == {}:
            self.setInitialState()
            ets = self.enabledTransitionsSet()

        n = 0
        if step is None:
            while(len(ets) != 0 and not n >= niter):
                duration, transition = self.oneFireSimulation(ets)

                n += 1

                self.currentClock += duration
                if self.currentClock < transition.minimumStartingTime:
                    raise ValueError('transition %s fired before his minimum starting time' % transition.name)

                if transition.show and show:
                    print transition.name + ' fired'
                    print 'currentTime : %s' % self.currentClock
                    print ''

        else:
            duration = 0.0
            while(len(ets) != 0 and not n >= niter):
                b = True
                while(b):
                    duration_, transition = self.oneFireSimulation(ets, duration)
                    n += 1

                    if transition is None:
                        b = False
                    else:
                        duration -= duration_
                    if transition.show and show:
                        print transition.name + ' fired'
                        print 'currentTime : %s' % self.currentClock
                        print ''
                    if not ets or n >= niter:
                        break

                if not ets or n >= niter:
                    break

            self.currentClock += step
            duration += step

        if show:
            print self.currentClock
        print 'end of the simulation'
