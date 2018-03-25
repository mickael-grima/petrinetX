import networkx

from fire_queues import DefaultFireQueue, TimeFireQueue
from nodes import Transition, Place
from rules import *


class Petrinet(networkx.DiGraph):
    """
    Represent a Petri-Net. Inherits from :class:`networkx.DiGraph`.
    Nodes are places and transitions.

    A Petrinet has a `fire_queue` attribute that inherits from
    :class:`FireQueue`.

    A Petrinet is initialized by an `adjacent_matrix`,
    """
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

    def make_rule_arg(self, arg):
        """
        If arg is a string and starts with `<class>::` for any existing class,
        then we create an object of this class. Otherwise we return arg.

        2 special cases:
          if the given class name is Transition or Place, the first given
          argument is its name, and we try to retrieve the corresponding
          transition or place from the nodes first.

        arg structure:
           <class>::<obj's name>

        :param arg: object
        :return:
        """
        if isinstance(arg, str) or isinstance(arg, unicode):
            try:
                class_name, obj_name = arg.split("::")
                if class_name == Place.__name__:
                    try:
                        return self.iter_places_by_name(obj_name).next()
                    except StopIteration:
                        return Place(name=obj_name)
                elif class_name == Transition.__name__:
                    try:
                        return self.iter_transitions_by_name(obj_name).next()
                    except StopIteration:
                        return Transition(name=obj_name)
                else:
                    return obj_name
            except:
                pass
        return arg

    def add_rules_to_node(self, node, rules):
        """
        add given rules to node.
        if rule_name is default, then add default rule.

        :param node: Place or Transition
        :param rules: {rule_name: rule_data}
        :return:
        """
        for rule_name, rule_data in (rules or {}).iteritems():
            args = map(
                self.make_rule_arg,
                rule_data.pop("args") if "args" in rule_data else ()
            )
            rule_data = {
                key: self.make_rule_arg(value)
                for key, value in rule_data.iteritems()
            }
            if rule_name == 'default':
                if isinstance(node, Transition):
                    node.remove_rule(self.DEFAULT_TRANSITION_RULE.__name__)
                    node.add_rule(
                        self.DEFAULT_TRANSITION_RULE, *args, **rule_data)
                elif isinstance(node, Place):
                    node.remove_rule(self.DEFAULT_PLACE_RULE.__name__)
                    node.add_rule(
                        self.DEFAULT_PLACE_RULE, *args, **rule_data)
            else:
                node.remove_rule(rule_name)
                node.add_rule(globals().get(rule_name), *args, **rule_data)

    @staticmethod
    def make_node(node, class_, attr=None):
        if isinstance(node, Place) or isinstance(node, Transition):
            return node
        if isinstance(node, str) or isinstance(node, unicode):
            return class_(name=node, **(attr or {}))

    def create_from_adj_dict(self, adj_dict):
        """
        example:
        {
            places: {
                place: {
                    attr: <arguments for place object>,
                    rules: {
                        <rule's name>: {
                            args=(),
                            attribute's name: attribute's value
                        }
                    },
                    tokens: <nb of tokens>
                },
                ...
            },
            transitions: {
                transition: {
                    attr: <arguments for place object>,
                    rules: {
                        <rule's name>: {
                            args=(),
                            attribute's name: attribute's value
                        }
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
        place_rules, transition_rules = {}, {}

        # first create places
        for place, data in adj_dict.get("places", {}).iteritems():
            places.setdefault(place, self.make_node(
                place, Place, attr=data.get("attr", {})))
            places[place].add_tokens(
                *[Token() for _ in range(data.get("tokens", 0))])
            place_rules[place] = data.get("rules")

        # first create transitions
        for transition, data in adj_dict.get("transitions", {}).iteritems():
            transitions.setdefault(transition, self.make_node(
                transition, Transition, attr=data.get("attr", {})))
            transition_rules[transition] = data.get("rules")

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

        # Add rules
        for place, prules in place_rules.iteritems():
            self.add_rules_to_node(places[place], prules)
        for transition, trules in transition_rules.iteritems():
            self.add_rules_to_node(transitions[transition], trules)

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

    def iter_token_places(self):
        """
        iterate places which contain tokens
        """
        for node in self.nodes.iterkeys():
            if isinstance(node, Place) and node.has_n_tokens():
                yield node

    def iter_transitions_by_name(self, transition_name):
        for node in self.nodes.iterkeys():
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
