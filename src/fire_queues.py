
import sys

from rules import TimeTransitionRule, TimePlaceRule


class FireQueue(list):
    """
    A FireQueue inherits from a list and contains transitions.
    If it is updated (sse :func:`update`), only transitions that are fire-able
    should be contained in this list.
    The first transition in this list is the next one to be fired.
    """
    def __init__(self, seq=()):
        super(FireQueue, self).__init__(seq)

    def insert_transition(self, transition, index=-1):
        if transition not in self:
            self.insert(index, transition)

    def is_empty(self):
        return len(self) == 0

    def next(self):
        try:
            return self.pop(0)
        except IndexError as e:
            raise StopIteration(e)

    def optimize(self):
        """
        Sort the transitions' list to have the "most fire-able" on first
        position
        """
        pass

    def update(self, *args, **kwargs):
        """
        Filter out the transition that are not fire-able
        """
        raise NotImplementedError()

    def pop_and_fire(self):
        """
        Pop the first transition of the list and make it fire.

        :return: transition
        """
        transition = self.next()
        transition.fire()
        return transition


class DefaultFireQueue(FireQueue):
    def update(self, *transitions, **kwargs):
        """
        transitions=list of transitions.
        Add new fire-able transitions and remove the old non-fire-able
        transitions
        """
        for transition in transitions:
            for place in transition.iter_places():
                for trans in place.iter_transitions():
                    if trans.is_fireable():
                        self.insert_transition(trans)

        index = 0
        while index < len(self):
            transition = self[index]
            if not transition.is_fireable():
                del self[index]
            else:
                index += 1


class TimeFireQueue(FireQueue):
    def __init__(self, seq=(), initial_clock=0):
        super(TimeFireQueue, self).__init__(seq)
        self.clock = initial_clock
        self.optimal_value = None

    def optimize(self):
        """
        for each transition get its value,
        and place the minimum value on top of the queue
        """
        values = {}
        index = 0
        while index < len(self):
            transition = self.pop(index)

            # Get value and insert transition on the right place
            transition_rule = transition.get_rule(TimeTransitionRule.__name__)
            if transition_rule is not None:
                value = transition_rule.get_value(self.clock)
                values[transition] = value
                i = 0
                while i < index:
                    if value <= values.get(self[i], sys.maxint):
                        break
                    i += 1
            else:
                i = index
            self.insert_transition(transition, i)

            index += 1
        self.optimal_value = values.get(self[0], 0) if self else 0
        self.clock += self.optimal_value

    def update(self, *args, **kwargs):
        """
        add transitions around every involved place to this FireQueue.
        Furthermore, every places should have their clock updated.
        """
        # add new transitions
        for transition in args:
            for place in transition.iter_places():
                for trans in place.iter_transitions():
                    if trans.is_fireable():
                        self.insert_transition(trans)

        # remove old transitions and set new global clock to every places
        index = 0
        while index < len(self):
            transition = self[index]
            if not transition.is_fireable():
                del self[index]
            else:
                for place in transition.iter_down_places():
                    place_rule = place.get_rule(TimePlaceRule.__name__)
                    place_rule.make_action(0, self.clock)
                index += 1

    def pop_and_fire(self):
        transition = self.next()
        transition.fire(self.clock)
        return transition
