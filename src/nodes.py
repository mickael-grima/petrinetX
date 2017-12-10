# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 17:55:32 2016

@author: Mickael Grima
"""
from rules import PlaceRule, TransitionRule, Rule
from tokens import Token
from utils import ensure_type

import logging

logger = logging.getLogger(__name__)


class Node:
    """ This class represents a node in the :class:`PetriNet <petrinet_simulator.PetriNet>`
        In particulary it the parent class of the classes :class:`Transition <petrinet_simulator.Transition>`
        and :class:`Place <petrinet_simulator.Place>`
    """

    def __init__(self, name=None):
        self.name = name
        """Name of the node
        """
        self.rules = []
        """Rules
        """

    def __repr__(self):
        return '<%s : %s>' % (self.__class__.__name__, self.name)

    @ensure_type(Rule)
    def add_rule(self, rule):
        self.rules.append(rule)


class Place(Node):
    def __init__(self, name=None):
        super(Place, self).__init__(name=name)
        self.__tokens = set()
        self.__up_transitions = {}
        self.__down_transitions = {}

    @ensure_type(Token)
    def add_token(self, token):
        self.__tokens.add(token)

    def remove_token(self, token):
        if self.has_token(token):
            self.__tokens.remove(token)

    def has_token(self, token):
        return token in self.__tokens

    def has_n_tokens(self, flow=1):
        return len(self.__tokens) >= flow

    def pop_n_tokens(self, flow=1):
        for _ in range(flow):
            self.__tokens.pop()

    @ensure_type(PlaceRule)
    def add_rule(self, rule):
        return super(Place, self).add_rule(rule)

    @ensure_type(Transition)
    def add_down_transition(self, transition, flow):
        self.__down_transitions[transition] = flow

    @ensure_type(Transition)
    def add_up_transition(self, transition, flow):
        self.__up_transitions[transition] = flow

    def iter_transitions(self):
        for transition, flow in self.__down_transitions.iteritems():
            yield transition, flow
        for transition, flow in self.__up_transitions.iteritems():
            yield transition, flow


class Transition(Node):
    def __init__(self, name=None):
        super(Transition, self).__init__(name=name)
        self.__down_places = {}
        self.__up_places = {}

    @ensure_type(Place)
    def add_down_place(self, place, flow=1):
        self.__down_places[place] = flow

    @ensure_type(Place)
    def add_up_place(self, place, flow=1):
        self.__up_places[place] = flow

    @ensure_type(TransitionRule)
    def add_rule(self, rule):
        return super(Transition, self).add_rule(rule)

    def iter_down_places(self):
        for place, flow in self.__down_places.iteritems():
            yield place, flow

    def iter_up_places(self):
        for place, flow in self.__up_places.iteritems():
            yield place, flow

    def iter_places(self):
        for item in self.iter_down_places():
            yield item
        for item in self.iter_up_places():
            yield item

    def fire(self):
        for rule in self.rules:
            rule.make_action()

    def is_fireable(self):
        """
        Define whether this transition can fire
        """
        return all(map(lambda r: r.is_satisfied(), self.rules))
