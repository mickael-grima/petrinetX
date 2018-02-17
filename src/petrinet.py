
import networkx

from fire_queues import DefaultFireQueue
from nodes import Transition, Place


class Petrinet(networkx.DiGraph):
    def __init__(self, adjacent_matrix, **attr):
        super(Petrinet, self).__init__(**attr)
        if isinstance(adjacent_matrix, dict):
            self.create_from_adj_dict(adjacent_matrix)
        elif isinstance(adjacent_matrix, list):
            self.create_from_adj_matrix(adjacent_matrix)
        elif adjacent_matrix is not None:
            raise TypeError("Adjacent matrix can't be of type %s"
                            % type(adjacent_matrix))
        # Next transition to fire
        self.fire_queue = DefaultFireQueue()

    @staticmethod
    def make_node(node, class_):
        if isinstance(node, Place) or isinstance(node, Transition):
            return node
        if isinstance(node, str) or isinstance(node, unicode):
            return class_(name=node)

    def create_from_adj_dict(self, adj_dict):
        places, transitions = {}, {}
        for place, trans in adj_dict.iteritems():
            for transition, flow in trans.iteritems():
                places.setdefault(place, self.make_node(place, class_=Place))
                transitions.setdefault(transition, self.make_node(
                    transition, class_=Transition))
                if flow > 0:
                    self.add_edge(
                        places[place], transitions[transition], flow=flow)
                elif flow < 0:
                    self.add_edge(
                        transitions[transition], places[place], flow=-flow)

    def create_from_adj_matrix(self, adj_matrix):
        """
        the rows represent the places
        the columns the transitions
        """
        places, transitions = {}, {}
        row = 0
        for flows in adj_matrix:
            column = 0
            places[row] = places.get(row, Place(name=row))
            for flow in flows:
                transitions[column] = transitions.get(
                    column, Transition(name=column))
                if flow > 0:
                    self.add_edge(places[row], transitions[column], flow=flow)
                elif flow < 0:
                    self.add_edge(transitions[column], places[row], flow=-flow)
                column += 1
            row += 1

    def add_node(self, node, **attr):
        super(Petrinet, self).add_node(node, **attr)
        if isinstance(node, Transition):
            self.fire_queue.insert_transition(node)

    def add_edge(self, u_of_edge, v_of_edge, **attr):
        flow = attr.get("flow", 1)
        if isinstance(u_of_edge, Transition) and isinstance(v_of_edge, Place):
            u_of_edge.add_up_place(v_of_edge, flow=flow)
            v_of_edge.add_down_transition(u_of_edge, flow=flow)
            return super(Petrinet, self).add_edge(u_of_edge, v_of_edge, **attr)
        if isinstance(u_of_edge, Place) and isinstance(v_of_edge, Transition):
            u_of_edge.add_up_transition(v_of_edge, flow=flow)
            v_of_edge.add_down_place(u_of_edge, flow=flow)
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
