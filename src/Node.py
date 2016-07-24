# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 17:55:32 2016

@author: Mickael Grima
"""

import logging


class Node:
    """ This class represents a node in the :class:`PetriNet <petrinet_simulator.PetriNet>`
        In particulary it the parent class of the classes :class:`Transition <petrinet_simulator.Transition>`
        and :class:`Place <petrinet_simulator.Place>`
    """
    def __init__(self, name='', logger=logging):
        self.name = name
        """Name of the node
        """
        self.idd = None
        """To difference the nodes if necessary
        """
        self.logger = logger

    def __repr__(self):
        return '<%s : %s>' % (self.__class__.__name__, self.name)
