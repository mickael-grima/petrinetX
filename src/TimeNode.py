# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 17:55:32 2016

@author: Mickael Grima
"""

import logging
from Node import Node


class TimeNode(Node):
    """ This class represents a node with time in the :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`
        It is the class parent of both classes :class:`TimePlace <petrinet_simulator.TimePlace>`
        and :class:`TimeTransition <petrinet_simulator.TimeTransition>`
        It herits from the parent class :class:`Node <petrinet_simulator.Node>`
    """
    def __init__(self, name='', logger=logging, time=0.0):
        super(TimeNode, self).__init__(name=name, logger=logger)
        if(time >= 0.0):
            self_time = time
        else:
            self_time = 0.0
        self.time = self_time
        """Default duration on the node
        """
