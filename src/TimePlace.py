# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 17:55:32 2016

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

from TimeNode import TimeNode
from Place import Place
import logging


class TimePlace(TimeNode, Place):
    """ This class represent a place in the class :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`
        It herits from both class :class:`TimeNode <petrinet_simulator.TimeNode>`
        and :class:`Place <petrinet_simulator.Place>`
    """
    def __init__(self, name='no name', logger=logging, time=0.0, withoutTime=False, withoutPriority=False, tokName=None,
                 exit=False):
        TimeNode.__init__(name=name, logger=logger, time=time)
        Place.__init__(self, name=name, logger=logger, withoutPriority=withoutPriority, tokName=tokName, exit=exit)
        self.withoutTime = withoutTime
        """ If True, the token arriving on this place have to reinitialize
            :attr:`placeClocks <petrinet_simulator.TimeToken.placeClocks>`
        """

    def copy(self):
        try:
            # Create the new place
            pl = TimePlace(self.name, self.time, self.withoutTime, self.withoutPriority, self.tokName, self.exit)

            # Adapte the token
            for tok in self.token:
                pl.token.append(tok.copy())

            return pl
        except:
            return None

    def addToken(self, token):
        assert token.__class__.__name__ == 'TimeToken'

        Place.addToken(self, token)
        if self.withoutTime:
            token.placeClocks = {}
            token.pclock = 0.0
        token.addPlaceClock(self, token.placeClocks.get(self))
        token.pclock = token.placeClocks[self]

    def getFirstToken(self, nb=1):
        """ Build a list of ``nb`` (or more) tokens with a token's :attr:`pclock <petrinet_simulator.TimeToken.pclock>`
            increasing order.

            :param nb: Length of the list
            :type nb: Int or long

            :returns: A sorted list of tokens
        """
        return sorted(self.token, key=lambda tok: tok.pclock)[:nb]

    def getPlaceTime(self):
        """ :returns: :attr:`time <petrinet_simulator.Place.time>`
        """
        return self.time

    def setWithoutTime(self, withoutTime):
        """ Set a value to the class's attribute :attr:`withoutTime <petrinet_simulator.Place.withoutTime>`

            :param withoutTime:
            :type withoutTime: Boolean
        """
        assert isinstance(withoutTime, bool)
        self.withoutTime = withoutTime
