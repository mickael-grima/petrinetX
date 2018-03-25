"""Contains Rules definitions.

.. moduleauthor:: Mickael Grima <mike.grima@hotmail.fr>
"""
import logging
from itertools import imap

from tokens import Token


logger = logging.getLogger(__name__)


class Rule(object):
    """
    A Rule object is mandatory for any Transition object.

    Any `Rule` object has an attribute `actor`. This `actor` can be either a
    :class:`Place` or a :class:`Transition`, and contains this rule.
    """
    def __init__(self, actor):
        self.actor = actor


class TransitionRule(Rule):
    """
    Transitions' rules should always inherit from this class.

    Before any fire, the :func:`is_satisfied` method is called. If this method
    returns `False`, the corresponding transition won't be able to fire. If it
    returns `True`, the rule's method :func:`make_action` can be called safely.

    If several transitions can fire at the same time, there are sorted
    considering the method :func:`get_value`.

    During a fire, every actors implied in the fire call their own rule's
    method :func:`make_action`.
    """
    def get_value(self, *args, **kwargs):
        return 0

    def is_satisfied(self, *args, **kwargs):
        raise NotImplementedError()

    def make_action(self, *args, **kwargs):
        raise NotImplementedError()


class PlaceRule(Rule):
    """
    Like the :class:`TransitionRule`, the `PlaceRule` has a method
    :func:`make_action`. This method can be called at anytime, but generally
    during a :class:`TransitionRule`'s :func:`make_action` call.

    If several `PlaceRule`classes are calling the method :func:`make_action`, a
    method :func:`get_value` is available to sort them.
    """
    def get_value(self, *args, **kwargs):
        return 0

    def make_action(self, *args, **kwargs):
        raise NotImplementedError()


class DefaultTransitionRule(TransitionRule):
    """
    This represent the default transition's rule:
    - To fire, the transition needs a given number of token on each of its
    down-places. This number of tokens is given for the construction of the
    petrinet. This transition is "fire-able" if and only if each down-place
    has at least the right number of tokens
    - During a fire, the transition calls every down-place and up-place's rules'
    method :func:`make_action`.

    .. note::
       If the down- and up-places have as rules only the
       :class:`DefaultPlaceRule`, then the firing is a classic petrinet's
       transition's firing.
    """
    def is_satisfied(self, *args, **kwargs):
        """
        returns `True` if and only if each down-place of the `actor`
        has at least the right number of tokens, given for the construction
        of the petrinet.
        """
        for place in self.actor.iter_down_places():
            if not place.has_n_tokens(self.actor.get_place_flow(place)):
                return False
        return True

    def make_action(self, *args, **kwargs):
        """
        Every down_place removes n tokens, where n is the flow between
        actor transition and current place

        Every up_place receives n tokens, where n is the flow between
        actor transition and current place

        .. important::
           1. **First** we c
           2.
        """
        for place in self.actor.iter_down_places():
            for rule in place.rules:
                rule.make_action(
                    -self.actor.get_place_flow(place), *args, **kwargs)

        for place in self.actor.iter_up_places():
            for rule in place.rules:
                rule.make_action(
                    self.actor.get_place_flow(place), *args, **kwargs)


class DefaultPlaceRule(PlaceRule):
    def make_action(self, tokens, *args, **kwargs):
        """
        If `tokens < 0`, pop `tokens` tokens from `actor`.
        If `tokens > 0`, add `tokens` new tokens on `actor`.

        :param tokens: `int`. Number of tokens. Can be negative.
        """
        if tokens < 0:
            self.actor.pop_n_tokens(-tokens)
        elif tokens > 0:
            self.actor.add_tokens(*[Token() for _ in range(tokens)])


class TimeTransitionRule(DefaultTransitionRule):
    def get_value(self, *args, **kwargs):
        """
        Each down_place may have a :class:`TimePlaceRule`'s rule. If it is the
        case, we call its :func:`get_value` method, and we call it
        `waiting_time`. Then return the maximum waiting_time.

        .. note::
           - If no down_place has a :class:`TimePlaceRule`'s rule, return 0.
           - The returned value is the waiting_time until the `actor` (which is
           a :class:`Transition`) is "fire-able".

        :return: `int`
        """
        waiting_time = 0
        for place in self.actor.iter_down_places():
            rule = place.get_rule(TimePlaceRule.__name__)
            if rule is not None:
                value = rule.get_value(self.actor.get_place_flow(place) - 1)
                if value is not None:
                    waiting_time = max(value, waiting_time)
        return waiting_time

    def make_action(self, clock, *args, **kwargs):
        """
        Every down_place removes n tokens, where n is the flow between
        actor transition and current place.

        Every up_place receives n tokens, where n is the flow between
        actor transition and current place.

        To remove or receive tokens, use place's rules.
        """
        for place in self.actor.iter_down_places():
            for rule in place.rules:
                rule.make_action(-self.actor.get_place_flow(place), clock)

        for place in self.actor.iter_up_places():
            for rule in place.rules:
                rule.make_action(self.actor.get_place_flow(place), clock)


class TimePlaceRule(PlaceRule):
    """
    A `TimePlaceRule` specifies 2 specific attributes:
       - `waiting_time`: how long should each token wait on this place before
                         leaving.
       - `global_clock`: A global time.
    """
    def __init__(self, actor, waiting_time=0, global_clock=0):
        super(TimePlaceRule, self).__init__(actor)
        # define how long should each token wait on this place
        self.waiting_time = waiting_time
        self.global_clock = global_clock

    def get_value(self, tokens, *args, **kwargs):
        """
        returns the tokens-th minimum waiting value.
        If tokens are missing, return None
        """
        try:
            return sorted(imap(
                lambda token: max(
                    self.global_clock - getattr(token, "clock", 0),
                    self.waiting_time),
                self.actor.iter_tokens()
            ), reverse=True)[tokens]
        except IndexError:
            return None

    def make_action(self, tokens, clock, *args, **kwargs):
        """
        send or receive tokens.
        Also update global clock

        :param clock: global clock
        :param tokens: integer.
                       -n: send n tokens.
                       0: send or receive nothing
                       n: receive n tokens
        """
        # remove tokens if needed
        if tokens < 0:
            self.actor.pop_n_tokens(-tokens)

        # update global clock
        self.global_clock = clock

        # Add new tokens if needed
        if tokens > 0:
            self.actor.add_tokens(*[Token(clock=clock) for _ in range(tokens)])


class BlockedFireRule(TransitionRule):
    """
    This rule blocks the transition's actor.
    A set of `blockers` is specified. If no other element is in `blockers` then
    the transition's actor can fire. Otherwise it can't
    """
    def __init__(self, actor):
        super(BlockedFireRule, self).__init__(actor)
        self.blockers = set()

    def is_satisfied(self, *args, **kwargs):
        """
        True if `blockers` is empty
        """
        return not self.blockers

    def make_action(self, blocker=None, block=True, **kwargs):
        """
        Add/Remove `blocker` to/from `blockers` if `block` is True/False

        :param blocker: object. Will be added or removed from `blockers`
        :param block: We add `blocker` to `blockers` if True,
                      otherwise we remove.
        """
        if blocker is not None:
            if block is True:
                self.blockers.add(blocker)
            elif blocker in self.blockers:
                self.blockers.remove(blocker)


class InheritanceRule(TransitionRule):
    """
    If the actor transition fires, apply one of the following logic
    depending on the `block` value:

    If `block` is True:
        - The actor transition blocks every transition in `targets`. Each of
          these transitions get a new :class:`BlockedFireRule` rule.

    If `block` is False:
        - The actor transition unblocks every transition in `targets`. Each of
          these transitions get a new :class:`BlockedFireRule` rule.

    .. important::
       :func:`make_action` will have an effect only one time.
    """
    def __init__(self, actor, block, *targets):
        super(InheritanceRule, self).__init__(actor)
        self.targets = set(targets)
        self.block = block
        for target in targets:
            target.add_rule(BlockedFireRule)
            rule = target.get_rule(BlockedFireRule.__name__)
            rule.make_action(self, block=self.block)

    def is_satisfied(self, *args, **kwargs):
        return True

    def make_action(self, *args, **kwargs):
        """
        Pop every transition from `targets` and call its
        :func:`BlockedFireRule.make_action` method.
        """
        while self.targets:
            target = self.targets.pop()
            rule = target.get_rule(BlockedFireRule.__name__)
            rule.make_action(self, block=not self.block)


class FireInheritanceRule(InheritanceRule):
    """
    :class:`InheritanceRule` with `block` set to True
    """
    def __init__(self, actor, *targets):
        super(FireInheritanceRule, self).__init__(actor, True, *targets)


class BlockingInheritanceRule(InheritanceRule):
    """
    :class:`InheritanceRule` with `block` set to False
    """
    def __init__(self, actor, *targets):
        super(BlockingInheritanceRule, self).__init__(actor, False, *targets)
