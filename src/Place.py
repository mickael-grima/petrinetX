# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 17:55:32 2016

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

from Node import Node, TimeNode
import logging


class Place(Node):
    """ This class represent a place in the class :class:`PetriNet <petrinet_simulator.PetriNet>`
        It is the class parent of class :class:`TimePlace <petrinet_simulator.TimePlace>`
        It herits from the parent class :class:`Node <petrinet_simulator.Node>`

        A place can contain several tokens, can have transitions as inputs and outputs, but no places
    """
    def __init__(self, name='', logger=logging, withoutPriority=False, tokName=None, exit=False):
        Node.__init__(self, name=name, logger=logger)
        self.token = []
        """ List of tokens currently on the place
        """
        self.withoutPriority = withoutPriority
        """ Boolean
            Can be:

               * ``True`` : If a token arrive on this place, all its priorities are deleted
               * ``False`` : Nothing happens
        """
        self.tokName = tokName
        """ The name of the tokens that arrive on this place. Their previous name is deleted
        """
        self.exit = exit
        """ Boolean
            Can be:

               * ``True`` : This place is considering as an exit place
               * ``False`` : This place is not an exit place
        """

    def __str__(self):
        return '%s, %s token(s)' % (self.name, len(self.token))

    def copy(self):
        """ Make a copy of ``place`` using :func:`TimeToken.copy <petrinet_simulator.TimeToken.copy>`

        :param place: place to copy
        :type place: :class:`Place <petrinet_simulator.Place>`

        :returns: An instance of the class :class:`Place <petrinet_simulator.Place>`
        """
        try:
            # Create new place
            pl = Place(self.name, self.withoutPriority, self.tokName, self.exit)

            # Adapte the list of tokens
            for tok in self.token:
                pl.token.append(tok.copy())

            return pl
        except:
            return None

    def addToken(self, token):
        """Add a token to the place

        :param token: token added on the place
        :type token: :class:`TimeToken <petrinet_simulator.TimeToken>`

        .. Warning:: We can NOT add twice the same token. In this case, to make a copy is necessary !
        """
        assert token.__class__.__name__ == 'Token'
        if token in self.token:
            self.logger.warning('Token %s already exists on the place %s' % (token.name, self.name))

        self.token.append(token)
        if self.withoutPriority:
            token.priority = {}
            token.priorityAfterFire = {}
            token.fireHeritance = {}
        if self.tokName is not None:
            token.name = self.tokName

    def removeToken(self, *tokens):
        """ Remove the given tokens of the place

            :param tokens: Token(s) to remove of the place
            :type tokens: *

            .. Note:: If a token is not from the class :class:`Token  <petrinet_simulator.Token>` a Warning is printed.
        """
        for token in tokens:
            if token in self.token:
                self.token.remove(token)
            else:
                self.logger.warning("Try to remove a token that doesn't exist on place %s" % self.name)

    def setWithoutPriority(self, withoutPriority):
        """ Set a value to the class's attribute :attr:`withoutPriority <petrinet_simulator.Place.withoutPriority>`

            :param withoutPriority:
            :type withoutPriority: Boolean
        """
        assert isinstance(withoutPriority, bool)
        self.withoutPriority = withoutPriority

    def setTokName(self, tokName):
        """ Set a value to the class's attribute :attr:`tokName <petrinet_simulator.Place.tokName>`

            :param tokName:
            :type tokName: String
        """
        assert isinstance(tokName, str)
        self.tokName = tokName


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
