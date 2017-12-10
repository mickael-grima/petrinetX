# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 17:55:32 2016

@author: Mickael Grima
"""
import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

from TimeNode import TimeNode
from Transition import Transition
import logging


class TimeTransition(Transition, TimeNode):
    """ This class represents a Transition with time in the class
        :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`
        It herits form both classes :class:`TimeNode <petrinet_simulator.TimeNode>` and
        :class:`Transition <petrinet_simulator.Transition>`

        This kind of transition has time's attribute
    """
    def __init__(self, name='', logger=logging, time=0.0, minimumStartingTime=-sys.maxint - 1, show=True):
        Transition.__init__(self, name=name, logger=logging, show=show)
        TimeNode.__init__(self, name=name, logger=logging, time=time)
        self.minimumStartingTime = minimumStartingTime
        """Transition can NOT fire before this time
        """

    def copy(transition):
        if not isinstance(transition, TimeTransition):
            raise TypeError('Transition expected, got a %s instead' % transition.__class__.__name__)

        tr = TimeTransition(transition.name, transition.time, transition.minimumStartingTime, transition.show)
        for tkns in transition.tokenQueue:
            tr.insertTokenQueue(tkns)
        for i in range(len(transition.tokenQueueAfterFire)):
            dct = transition.tokenQueueAfterFire[i]
            for key, dc in dct.items():
                for t, attr in dc.items():
                    for tkns in attr['tokenQueue']:
                        tokenNames = []
                        for tkn in tkns:
                            tokenNames.append(tkn)
                        tr.insertTokenQueueAfterFire(tokenNames, t, key, i=i, place_presence=attr['place_presence'],
                                                     nb_tok=attr['nb_tok'])
        return tr

    def getTransitionTime(self):
        """ :returns: :attr:`time <petrinet_simulator.Transition.time>`
        """
        return self.time
