# -*- coding: utf-8 -*-
"""
Contains Transition and Place definitions.
"""
from rules import DefaultTransitionRule


class Node(object):
    def __init__(self):
        self.rules = []

    def add_rule(self, rule, *args, **kwargs):
        """
        Rule's actor should be node itself

        :param rule: class object
        :param args:
        :param kwargs:
        :return:
        """
        self.rules.append(rule(self, *args, **kwargs))


class Place(Node):
    def __init__(self):
        super(Place, self).__init__()
        self.__tokens = set()
        self.__up_transitions = {}
        self.__down_transitions = {}

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
        tokens = set()
        for _ in range(min(flow, len(self.__tokens))):
            tokens.add(self.__tokens.pop())
        return tokens

    def add_down_transition(self, transition, flow=1):
        self.__down_transitions[transition] = flow

    def add_up_transition(self, transition, flow=1):
        self.__up_transitions[transition] = flow

    def iter_transitions(self):
        for transition, _ in self.__down_transitions.iteritems():
            yield transition
        for transition, _ in self.__up_transitions.iteritems():
            yield transition


class Transition(Node):
    def __init__(self, default=True):
        """
        If default is set to True, we append DefaultTransitionRule in the
        rules' list

        :param default: boolean
        """
        super(Transition, self).__init__()
        if default is True:
            self.add_rule(DefaultTransitionRule)

        self.__down_places = {}
        self.__up_places = {}

    def add_down_place(self, place, flow=1):
        self.__down_places[place] = flow

    def add_up_place(self, place, flow=1):
        self.__up_places[place] = flow

    def get_place_flow(self, place):
        if place in self.__down_places:
            return self.__down_places[place]
        if place in self.__up_places:
            return self.__up_places[place]
        return 0

    def iter_down_places(self):
        for place, flow in self.__down_places.iteritems():
            yield place

    def iter_up_places(self):
        for place, flow in self.__up_places.iteritems():
            yield place

    def iter_places(self):
        for place in self.iter_down_places():
            yield place
        for place in self.iter_up_places():
            yield place

    def fire(self):
        for rule in self.rules:
            rule.make_action()

    def is_fireable(self):
        """
        Define whether this transition can fire
        """
        return all(map(lambda r: r.is_satisfied(), self.rules))
