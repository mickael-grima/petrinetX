import networkx

from fire_queues import DefaultFireQueue, TimeFireQueue
from nodes import Transition, Place
from tokens import Token
from rules import DefaultPlaceRule, DefaultTransitionRule, TimePlaceRule, \
    TimeTransitionRule


class Petrinet(networkx.DiGraph):
    DEFAULT_PLACE_RULE = DefaultPlaceRule
    DEFAULT_TRANSITION_RULE = DefaultTransitionRule
    DEFAULT_FIRE_QUEUE = DefaultFireQueue

    def __init__(self, adjacent_matrix, fire_queue=None, **attr):
        # Next transition to fire
        self.fire_queue = fire_queue if fire_queue is not None else self.DEFAULT_FIRE_QUEUE()
        super(Petrinet, self).__init__(**attr)
        if isinstance(adjacent_matrix, dict):
            self.create_from_adj_dict(adjacent_matrix)
        elif isinstance(adjacent_matrix, list):
            self.create_from_adj_matrix(adjacent_matrix)
        elif adjacent_matrix is not None:
            raise TypeError("Adjacent matrix can't be of type %s"
                            % type(adjacent_matrix))

    @classmethod
    def add_rules_to_node(cls, node, rules):
        """
        add given rules to node.
        if rule_name is default, then add default rule.

        :param node: Place or Transition
        :param rules: {rule_name: rule_data}
        :return:
        """
        for rule_name, rule_data in (rules or {}).iteritems():
            if rule_name == 'default':
                if isinstance(node, Transition):
                    node.add_rule(cls.DEFAULT_TRANSITION_RULE, **rule_data)
                elif isinstance(node, Place):
                    node.add_rule(cls.DEFAULT_PLACE_RULE, **rule_data)
            else:
                node.add_rule(globals().get(rule_name), **rule_data)

    @classmethod
    def make_node(cls, node, class_, attr=None, rules=None):
        if isinstance(node, Place) or isinstance(node, Transition):
            cls.add_rules_to_node(node, rules)
            return node
        if isinstance(node, str) or isinstance(node, unicode):
            node_ = class_(name=node, **(attr or {}))
            cls.add_rules_to_node(node_, rules)
            return node_

    def create_from_adj_dict(self, adj_dict):
        """
        example:
        {
            places: {
                place: {
                    attr: <arguments for place object>,
                    rules: {
                        <rule's name>: {attribute's name: attribute's value}
                    },
                    tokens: <nb of tokens>
                },
                ...
            },
            transitions: {
                transition: {
                    attr: <arguments for place object>,
                    rules: {
                        <rule's name>: {attribute's name: attribute's value}
                    }
                },
                ...
            },
            graph: {
                place: {
                    transition: flow (
                        < 0: place is up to transition;
                        > 0: place is down to transition
                    )
                }
            }
        }

        :param adj_dict:
        :return:
        """
        places, transitions = {}, {}

        # first create places
        for place, data in adj_dict.get("places", {}).iteritems():
            places.setdefault(place, self.make_node(
                place, Place,
                attr=data.get("attr", {}),
                rules=data.get("rules", {})))
            places[place].add_tokens(
                *[Token() for _ in range(data.get("tokens", 0))])

        # first create transitions
        for transition, data in adj_dict.get("transitions", {}).iteritems():
            transitions.setdefault(transition, self.make_node(
                transition, Transition,
                attr=data.get("attr", {}),
                rules=data.get("rules", {})))

        # create the corresponding graph
        for place, trans in adj_dict["graph"].iteritems():
            places.setdefault(place, self.make_node(place, Place))
            for transition, flow in trans.iteritems():
                transitions.setdefault(transition, self.make_node(
                    transition, Transition))
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

    def iter_places_by_name(self, place_name):
        for node in self.nodes.iterkeys():
            if isinstance(node, Place) and node.name == place_name:
                yield node

    def iter_transitions_by_name(self, transition_name):
        for node in self.nodes.itervalues():
            if isinstance(node, Transition) and node.name == transition_name:
                yield node

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
    DEFAULT_FIRE_QUEUE = TimeFireQueue
