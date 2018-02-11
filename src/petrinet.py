
from fire_queues import DefaultFireQueue


class BasePetrinet(object):
    def __init__(self):
        self.places = set()
        self.transitions = set()

        # Next transition to fire
        self.fire_queue = DefaultFireQueue()

    def add_transition(self, transition):
        self.transitions.add(transition)
        self.fire_queue.insert_transition(transition)

    def add_place(self, place):
        self.places.add(place)

    def is_blocked(self):
        return self.fire_queue.is_empty()

    def update_fire_queue(self, transition):
        for place in transition.iter_places():
            for trans in place.iter_transitions():
                self.fire_queue.insert_transition(trans)

    def next(self):
        transition = self.fire_queue.next()
        transition.fire()
        self.update_fire_queue(transition)
        self.fire_queue.optimize()

    def simulate(self):
        self.fire_queue.optimize()
        while not self.is_blocked():
            self.next()
