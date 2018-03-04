
import logging
from itertools import imap

from tokens import Token


logger = logging.getLogger(__name__)


class Rule(object):
    """
    A Rule object is mandatory for any Transition object.
    Before any fire, the `is_satisfied` method is called.
    After a fire, every actors implied in the fire
    call their own rule's `make_action` method.
    """

    def __init__(self, actor):
        self.actor = actor
        pass


class TransitionRule(Rule):
    def get_value(self, *args, **kwargs):
        return 0

    def is_satisfied(self, *args, **kwargs):
        raise NotImplementedError()

    def make_action(self, *args, **kwargs):
        raise NotImplementedError()


class PlaceRule(Rule):
    def get_value(self, *args, **kwargs):
        return 0

    def make_action(self, *args, **kwargs):
        raise NotImplementedError()


class DefaultTransitionRule(TransitionRule):
    def is_satisfied(self, *args, **kwargs):
        """
        If at least one down place has one token, returns True
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
        if tokens < 0:
            self.actor.pop_n_tokens(-tokens)
        elif tokens > 0:
            self.actor.add_tokens(*[Token() for _ in range(tokens)])


class TimeTransitionRule(DefaultTransitionRule):
    def get_value(self, *args, **kwargs):
        """
        The value here is the minimum waiting time before next possible fire.
        This waiting time is the min(max(dow_places.waiting_time))
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
        :return:
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
    def __init__(self, actor):
        super(BlockedFireRule, self).__init__(actor)
        self.blockers = set()

    def is_satisfied(self, *args, **kwargs):
        return not self.blockers

    def make_action(self, blocker=None, block=True, **kwargs):
        if blocker is not None:
            if block is True:
                self.blockers.add(blocker)
            elif blocker in self.blockers:
                self.blockers.remove(blocker)


class InheritanceRule(TransitionRule):
    """
    If the actor transition fires, it allows every targeted transitions to fire
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
        while self.targets:
            target = self.targets.pop()
            rule = target.get_rule(BlockedFireRule.__name__)
            rule.make_action(self, block=not self.block)


class FireInheritanceRule(InheritanceRule):
    def __init__(self, actor, *targets):
        super(FireInheritanceRule, self).__init__(actor, True, *targets)


class BlockingInheritanceRule(InheritanceRule):
    def __init__(self, actor, *targets):
        super(BlockingInheritanceRule, self).__init__(actor, False, *targets)
