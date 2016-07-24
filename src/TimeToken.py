# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 14:54:37 2016

@author: Mickael Grima
"""

from Token import Token
from utils.tools import pref_func
import logging


class TimeToken(Token):
    """This class represent a token with time. It herits from the parent class :class:`Token <petrinet_simulator.Token>`
    """
    def __init__(self, name='no name', logger=logging, show=True, fire=True):
        Token.__init__(self, name=name, logger=logger, show=show, fire=fire)
        self.placeClocks = {}
        """ We save inside a place as key and associated to this place the time that the token will live on this place.
            We can add a place's clock using the method addPlaceClock()
        """
        self.transitionClocks = {}
        """ We save inside a transition as key and associated to this transition the time that the token will live
            on this transition. We can add a transition's clock using the method addTransitionClock()
        """
        self.pclock = 0.0
        """ It represents the time that the tokens lived on the current place on the TimedPetriNet during a simulation.
            It is reinitialized to 0.0 when the token change its current place
        """
        self.tclock = {}
        """ It represents the time that the tokens lived on the current transitions on the TimedPetriNet
            during a simulation. Only the transition that can fire this token are save inside
        """
        self.currentClock = 0.0
        """It represents how much time lived the token in the TimedPetriNet during a simulation
        """
        self.minimumStartingTime = {}
        """The token can't be fired by the given transition before the associated time
        """

    def copy(self):
        try:
            # The new token
            tok = TimeToken(self.name, self.show, self.fire)

            # adapte pclock
            tok.pclock = self.pclock

            # Adapte currentClock
            tok.currentClock = self.currentClock

            # Adapte placeClocks
            for place, clock in self.placeClocks.iteritems():
                tok.addPlaceClock(place, clock)

            # Adapte transitionClocks
            for transition, clock in self.transitionClocks.iteritems():
                tok.addTransitionClock(transition, clock)

            # adapte tclock
            for transition, clock in self.tclock.iteritems():
                tok.tclock.setdefault(transition, clock)

            # Adapte priority
            for place, attr in self.priority.iteritems():
                tok.addPriority(place, attr['priority'], attr['pref'])

            # adapte priorityAfterFire
            for transition, dct in self.priorityAfterFire.iteritems():
                for loc, prt in dct.iteritems():
                    for pl, attr in prt.iteritems():
                        tok.addPriorityAfterFire(transition, {pl: attr['priority']}, location=loc, pref=attr['pref'])

            # adapte fireHeritance
            for transition, attr in self.fireHeritance.iteritems():
                for place, toks in attr.iteritems():
                    for tk in toks:
                        tok.addFireHeritance(tk, place, transition)

            return tok
        except:
            return None

    def addPlaceClock(self, place, clock=None):
        """ Add a place Clock to ``place``.

        :param place: place where token would wait
        :type place: :class:`Place <petrinet_simulator.Place>`

        * options:

          * ``clock = None`` : the duration that the token would wait on ``place``.
            If None then we consider the place's :attr:`time <petrinet_simulator.Place.time>`.

        .. Note:: If a place's clock already exists for ``place``, we add ``clock`` only if its value is higher
        """
        assert place.__class__.__name__ == 'Place'

        if self.placeClocks.get(place) is None:
            if clock is None:
                self.placeClocks.setdefault(place, place.getPlaceTime())
            else:
                self.placeClocks.setdefault(place, clock)
        else:
            if clock is None:
                t = place.getPlaceTime()
            if t > self.placeClocks[place]:
                self.placeClocks[place] = t
            else:
                if(clock > self.placeClocks[place]):
                    self.placeClocks[place] = clock

    def addTransitionClock(self, transition, clock=None):
        """Add a transition Clock to :attr:`transitionClocks <petrinet_simulator.TimeToken.transitionClocks>`.

        :param transition: transition where token would wait
        :type transition: :class:`Transition <petrinet_simulator.Transition>`

        * options:

          * ``clock = None`` : the duration that the token would wait on ``transition``.
            If None then we consider the transition's :attr:`time <petrinet_simulator.Transition.time>`.

        .. Note:: If a transition's clock already exists for ``transition``,
                  we add ``clock`` only if its value is higher
        """
        assert transition.__class__.__name__ == 'Transition'

        if self.transitionClocks.get(transition) is None:
            if clock is None:
                self.transitionClocks.setdefault(transition, transition.getTransitionTime())
            else:
                self.transitionClocks.setdefault(transition, clock)
        else:
            if clock is None:
                t = transition.getTransitionTime()
            if t > self.transitionClocks[transition]:
                self.transitionClocks[transition] = t
            else:
                if clock > self.transitionClocks[transition]:
                    self.transitionClocks[transition] = clock

    def addMinimumStartingTime(self, transition, time):
        """ If a time already exists for ``transition`` we replace it by the given time

        :param transition:
        :type transition: :class:`Transition <petrinet_simulator.Transition>`
        :param time:
        :type time: int, long or float

        .. Note:: If a transition's minimumStartingTime already exists for ``transition``,
                  we add ``time`` only if its value is higher
        """
        assert transition.__class__.__name__ == 'Transition'
        if self.minimumStartingTime.get(transition) is None:
            if time is not None:
                self.minimumStartingTime.setdefault(transition, time)
            else:
                self.minimumStartingTime.setdefault(transition, transition.minimumStartingTime)
        else:
            mt = self.minimumStartingTime[transition]
            if time is not None:
                if time > mt:
                    self.minimumStartingTime[transition] = time
            else:
                if transition.minimumStartingTime > mt:
                    self.minimumStartingTime[transition] = transition.minimumStartingTime

    def get_priority_value(self, place, transition, time=0):
        """ Compute a priority value for ``token``. Given two tokens, the one with the biggest priority_value is fired first
            if ``transition`` is not a priority for ``token`` on ``place``, we return 0

            :param place: *
            :type place: :class:`Place <Place.Place>`
            :param transition: *
            :type transition: :class:`Transition <Transition.Transition>`

            :returns: A float bigger or equal to 0
        """
        return (pref_func(time), super(TimeToken, self).get_priority_value(place, transition)[1])
