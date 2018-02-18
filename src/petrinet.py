import networkx

from fire_queues import DefaultFireQueue
from nodes import Transition, Place
from rules import DefaultPlaceRule, DefaultTransitionRule, TimePlaceRule, \
    TimeTransitionRule


class Petrinet(networkx.DiGraph):
    DEFAULT_PLACE_RULE = DefaultPlaceRule
    DEFAULT_TRANSITION_RULE = DefaultTransitionRule

    def __init__(self, adjacent_matrix, **attr):
        # Next transition to fire
        self.fire_queue = DefaultFireQueue()
        super(Petrinet, self).__init__(**attr)
        if isinstance(adjacent_matrix, dict):
            self.create_from_adj_dict(adjacent_matrix)
        elif isinstance(adjacent_matrix, list):
            self.create_from_adj_matrix(adjacent_matrix)
        elif adjacent_matrix is not None:
            raise TypeError("Adjacent matrix can't be of type %s"
                            % type(adjacent_matrix))

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
        if isinstance(node, Transition):
            node.add_rule(self.DEFAULT_TRANSITION_RULE)
            self.fire_queue.insert_transition(node)
        elif isinstance(node, Place):
            node.add_rule(self.DEFAULT_PLACE_RULE)
        else:
            raise TypeError("node should be of type Place or Transition."
                            "type=%s found instead" % type(node))
        super(Petrinet, self).add_node(node, **attr)

    def add_edge(self, u_of_edge, v_of_edge, **attr):
        flow = attr.get("flow", 1)
        if isinstance(u_of_edge, Transition) and isinstance(v_of_edge, Place):
            u_of_edge.add_up_place(v_of_edge, flow=flow)
            v_of_edge.add_down_transition(u_of_edge, flow=flow)
            self.add_node(u_of_edge)
            self.add_node(v_of_edge)
            return super(Petrinet, self).add_edge(u_of_edge, v_of_edge, **attr)
        if isinstance(u_of_edge, Place) and isinstance(v_of_edge, Transition):
            u_of_edge.add_up_transition(v_of_edge, flow=flow)
            v_of_edge.add_down_place(u_of_edge, flow=flow)
            self.add_node(u_of_edge)
            self.add_node(v_of_edge)
            return super(Petrinet, self).add_edge(u_of_edge, v_of_edge, **attr)
        raise TypeError("edge between %s and %s is not possible"
                        % (type(u_of_edge), type(v_of_edge)))

    def is_blocked(self):
        return self.fire_queue.is_empty()

    def next(self):
        transition = self.fire_queue.pop_and_fire()
        self.fire_queue.update(transition)
        self.fire_queue.optimize()

    def simulate(self):
        self.fire_queue.update()
        self.fire_queue.optimize()
        while not self.is_blocked():
            self.next()


class TimePetrinet(Petrinet):
    DEFAULT_PLACE_RULE = TimePlaceRule
    DEFAULT_TRANSITION_RULE = TimeTransitionRule
