
import networkx

from fire_queues import DefaultFireQueue
from nodes import Transition, Place


class Petrinet(networkx.DiGraph):
    def __init__(self, **attr):
        super(Petrinet, self).__init__(**attr)
        # Next transition to fire
        self.fire_queue = DefaultFireQueue()

    def add_node(self, node, **attr):
        super(Petrinet, self).add_node(node, **attr)
        if isinstance(node, Transition):
            self.fire_queue.insert_transition(node)

    def add_edge(self, u_of_edge, v_of_edge, **attr):
        if isinstance(u_of_edge, Transition) and isinstance(v_of_edge, Place):
            u_of_edge.add_up_place(v_of_edge)
            v_of_edge.add_down_transition(u_of_edge)
            return super(Petrinet, self).add_edge(u_of_edge, v_of_edge, **attr)
        if isinstance(u_of_edge, Place) and isinstance(v_of_edge, Transition):
            u_of_edge.add_up_transition(v_of_edge)
            v_of_edge.add_down_place(u_of_edge)
            return super(Petrinet, self).add_edge(u_of_edge, v_of_edge, **attr)
        raise TypeError("edge between %s and %s is not possible"
                        % (type(u_of_edge), type(v_of_edge)))

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
