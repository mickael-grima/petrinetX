
import logging

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

    def is_satisfied(self):
        return True

    def make_action(self, *args, **kwargs):
        pass


class TransitionRule(Rule):
    pass


class PlaceRule(Rule):
    pass


class DefaultTransitionRule(TransitionRule):
    def is_satisfied(self):
        """
        If at least one down place has one token, returns True
        """
        for place in self.actor.iter_down_places():
            if not place.has_n_tokens(self.actor.get_place_flow(place)):
                return False
        return True

    def make_action(self):
        """
        Take any down place, remove one token,
        and add this token to any up_place

        This function can be called only if `is_satisfied` return True.
        A token will always be found
        """
        for place in self.actor.iter_down_places():
            place.pop_n_tokens(self.actor.get_place_flow(place))

        for place in self.actor.iter_up_places():
            place.add_tokens(
                *[Token() for _ in range(self.actor.get_place_flow(place))])


class DefaultPlaceRule(PlaceRule):
    def make_action(self, flow=1):
        pass
