# -*- coding: utf-8 -*-
"""Contains Transition and Place definitions.

.. moduleauthor:: Mickael Grima <mike.grima@hotmail.fr>
"""
from rules import PlaceRule, TransitionRule


class Node(object):
    """Parent class of :class:`Transition` and :class:`Place`.

    A Node object has two main attributes:
    - `name` (str): the node's name
    - `rules` (list): list of rules.

    .. important::
       `rules` contains the node's rule. If the node object is a :class:`Place`,
       rules can only be subclass of :class:`PlaceRule`. If the node is a
       :class:`Transition`, rules can only be subclass of
       :class:`TransitionRule`.
    """
    def __init__(self, name=None):
        """

        :param name (str): node's name
        """
        self.name = name
        self.rules = []

    def add_rule(self, rule, *args, **kwargs):
        """
        `rule`'s actor should be node itself.

        `rule` is added to `rules` list only if no other rule of the same class
        exists in `rules`.

        :param rule: class object.
        :param args: arguments to pass to `rule`
        :param kwargs: key arguments to pass to `rule`
        """
        if issubclass(self.__class__, Place) and not issubclass(
                rule, PlaceRule):
            return
        if issubclass(self.__class__, Transition) and not issubclass(
                rule, TransitionRule):
            return

        if rule.__name__ not in map(
                lambda r: r.__class__.__name__, self.rules):
            self.rules.append(rule(self, *args, **kwargs))

    def get_rule(self, rule_name):
        """
        If it exists, returns the rule in `rules` whose class' name is
        `rule_name`.

        :param rule_name: (str) rule's class' name
        :return: a rule.
        """
        for rule in self.rules:
            if rule.__class__.__name__ == rule_name:
                return rule

    def remove_rule(self, rule_name):
        """
        If it exists, deletes the rule in `rules` whose class' name is
        `rule_name`.

        :param rule_name: (str) rule's class' name
        :return: a rule.
        """
        i = 0
        for rule in self.rules:
            if rule_name == rule.__class__.__name__:
                break
            i += 1

        if i < len(self.rules):
            del self.rules[i]


class Place(Node):
    """Inherits from class :class:`Node`.

    `Place` object can also contains tokens. If it contains a token, we say that
    token is on `Place`.
    It also has down- and up-transitions. A place always receives tokens from
    the down-transition, whenever this last one fires, and always gives tokens
    to an up-transition, whenever this last one fires. This is a default rule
    which can be changed by defining new `Rule` objects.
    """
    def __init__(self, name=None):
        super(Place, self).__init__(name=name)
        self.__tokens = set()
        self.__up_transitions = {}
        self.__down_transitions = {}

    def add_tokens(self, *tokens):
        """
        Add the `tokens` to this place.

        :param tokens: tuple of tokens
        :return:
        """
        self.__tokens.update(tokens)

    def remove_token(self, token):
        """
        if it exists, remove `token` from place.

        :param token: of class :class:`Token`
        :return:
        """
        if self.has_token(token):
            self.__tokens.remove(token)

    def has_token(self, token):
        """
        Returns `True` if it has `token`, `False` otherwise.

        :param token: of class :class:`Token`
        :return:
        """
        return token in self.__tokens

    def has_n_tokens(self, flow=1):
        """
        Returns `True` if this place has `flow` tokens or more, `False` otherwise.

        :param flow: `int`. Indicates the number of tokens.
        :return: `bool`
        """
        return len(self.__tokens) >= flow

    def pop_n_tokens(self, flow=1):
        """
        Removes and returns `flow` tokens. If this place has less than `flow`
        tokens, removes and returns every tokens.

        :param flow: `int`. Indicates the number of tokens.
        :return: `set` of tokens.
        """
        tokens = set()
        for _ in range(min(flow, len(self.__tokens))):
            tokens.add(self.__tokens.pop())
        return tokens

    def iter_tokens(self):
        """
        Iterates every token on this place.

        :return: `iter`
        """
        for token in self.__tokens:
            yield token

    def add_down_transition(self, transition, flow=1):
        """
        As a default petrinet's rule, if `transition` fires, receives `flow`
        tokens from this `transition`.

        :param transition:
        :param flow: `int`. Indicates the number of tokens.
        """
        self.__down_transitions[transition] = flow

    def add_up_transition(self, transition, flow=1):
        """
        As a default petrinet's rule, if `transition` fires, removes `flow`
        tokens and sends it to other `transition`'s up-places.

        :param transition:
        :param flow: `int`. Indicates the number of tokens.
        """
        self.__up_transitions[transition] = flow

    def iter_transitions(self):
        """
        Iterates every down- and up-transitions to this place.

        :return: iterator
        """
        for transition, _ in self.__down_transitions.iteritems():
            yield transition
        for transition, _ in self.__up_transitions.iteritems():
            yield transition


class Transition(Node):
    """
    A transition is the main piece in a petrinet. As a child of class
    :class:`Node`, any transition can have rules.

    In the same meaning as for the class :class:`Place`, a `Transition` object
    can have down- and up-places that respectively sends/receives tokens from
    this `transition`.

    To make any action on its down- and up-places, the `Transition` object has
    to be "fire-able". Once a transition is "fire-able", it can fire.
    In this case, actions may be made on the down- and up-places, as removing or
    sending from/to these places.

    The two main methods for a `Transition` object are:
    - :func:`is_fireable`: returns `True` if every rule stored in the `Node`'s
    attribute `rules` is satisfied, that can be check calling the rule's method
    :func:`is_satisfied`.
    - :func:`fire`: calls every rule's method :func:`make_action`. As these
    rules are satisfied, :func:`make_action` should never fail.
    """
    def __init__(self, name=None):
        super(Transition, self).__init__(name=name)

        self.__down_places = {}
        self.__up_places = {}

    def add_down_place(self, place, flow=1):
        """
        Set `place` as a down-place of this transition.

        :param place:
        :param flow: `int`. Indicates the number of tokens.
        :return:
        """
        self.__down_places[place] = flow

    def add_up_place(self, place, flow=1):
        """
        Set `place` as a up-place of this transition.

        :param place:
        :param flow: `int`. Indicates the number of tokens.
        :return:
        """
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

    def fire(self, *args, **kwargs):
        """
        Make a fire action.

        Firing means that every rule stored in the :class:`Node`'s attribute
        `rules` call its method :func:`make_action`. This method never fails
        since a rule that call this method is always "satisfied".

        :param args:
        :param kwargs:
        """
        for rule in self.rules:
            rule.make_action(*args, **kwargs)

    def is_fireable(self):
        """
        Returns `True` if this transition can fire, `False` otherwise.

        A transition can fire if its rules are all satisfied.
        To check whether a rule is satisfied, one can call the rule's
        method :func:`is_satisfied`.
        :return: boolean
        """
        return all(map(lambda r: r.is_satisfied(), self.rules))
