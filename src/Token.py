# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 14:54:37 2016

@author: Mickael Grima
"""

from utils.tools import pref_func
import logging


class Token:
    """This class represent a token.

    A token is an object that moves in the Petrinet. It stays on :class:`places <petrinet_simulator.Place>`
    and may change its place when a :class:`transition <petrinet_simulator.Transition>` fire

    The token object contains the necessary informations to know how to fire this token in the petrinet.
    It can have priority transitions or fire heritance to impose an order for the firing token.
    """

    def __init__(self, name='no name', logger=logging, show=True, fire=True):
        self.name = name
        """ If several tokens are firing by the same transition,
            the result is then a new token whose name is an union
            of the previous token's names, separate by a '_'

            .. Warning:: A token's name must not have an '_' in its name
        """
        self.show = show
        self.fire = fire
        """ If ``True`` the token can be fired, else not
        """
        self.priority = {}
        """ list of priority transitions on a given place:
            if our token is on this place he can be fired only by one of these transitions,
            with a preference with the first transitions. We can add a priority on a given place
            using the method :func:`addPriority() <petrinet_simulator.Token.addPriority>`
        """
        self.priorityAfterFire = {}
        """ If our token is fired by the transition, then we add to the given token the given priority.
            This parameter is usefull to add priorities dynamically. We can add a priorityAfterFire on a given place
            using the method :func:`addPriorityAfterFire() <petrinet_simulator.Token.addPriorityAfterFire>`
        """
        self.fireHeritance = {}
        """ If our token is fired by a transition, then we search on each place the token whose name contains one
            of the strings in the associated list, i.e one of these strings is in ``token.name.split('_')``.
            Then we change the fire parameter of these tokens in True. We can add a fireHeritance for a given transition
            using the method :func:`addFireHeritance() <petrinet_simulator.Token.addFireHeritance>`
        """
        self.logger = logger

    def __str__(self):
        return ', '.join(self.name.split('_'))

    def __repr__(self):
        return '<Token : %s>' % str(self)

    def copy(self):
        """Make a copy of a token

        :param token: token to copy
        :type token: :class:`Token <petrinet_simulator.Token>`

        :returns: An instance of the class :class:`Token <petrinet_simulator.Token>`

        .. Warning:: Transition and place are shared !
                 If the variable is not a token, the method
                 raise an exception
        """
        try:
            tok = Token(self.name, self.show, self.fire)
            for place, attr in self.priority.iteritems():
                tok.addPriority(place, attr['priority'], attr['pref'])
            for transition, dictionnary in self.priorityAfterFire.iteritems():
                for loc, prt in dictionnary.iteritems():
                    tok.addPriorityAfterFire(transition, prt, loc)
            for transition, attr in self.fireHeritance.iteritems():
                for place, toks in attr.iteritems():
                    for tk in toks:
                        tok.addFireHeritance(tk, place, transition)
            return tok
        except:
            return None

    def addPriority(self, place, pref='time', *transitions):
        """ Add priority for ``place``

        :param place: place where the priority is effectiv
        :type place: :class:`Place <petrinet_simulator.Place>`
        :param transitions: list of priority transition(s)
        :type transitions: list

        * options:

            * ``pref = 'time'``: We have two choices:

            * ``'time'``: the priority is first the time: among the transitions in ``transitions``,
                          we choose first the ones that can fire in the minimum time, and then the ones
                          that are the lowest indice in ``transitions``
            * `anything else`: Only the first transition can fire. It is deleted of priority's queue after the fire

        **Example:**

        >>> import petrinet_simulator as pns
        >>>
        >>> token = pns.Token(name = 'token')
        >>> place1 = pns.Place(name = 'place1')
        >>> place2 = pns.Place(name = 'place2')
        >>> trans1 = pns.Transition(name = 'tr1')
        >>> trans2 = pns.Transition(name = 'tr2')
        >>>
        >>> token.addPriority(place1, trans1)
        >>> token.addPriority(place2, [trans2,trans1], pref='pref')
        >>>
        >>> token.print_priority() #doctest: +NORMALIZE_WHITESPACE
        # <Place : place2> --> [<Transition : tr2>, <Transition : tr1>](pref=pref) #
        # <Place : place1> --> [<Transition : tr1>](pref=time) #

        """
        if self.priority.get(place) is None:
            self.priority.setdefault(place, {'priority': [], 'pref': pref})
        for t in transitions:
            self.priority[place]['priority'].append(t)
            self.priority[place]['pref'] = pref

    def addPriorityAfterFire(self, transition, priority, location='self', pref='time'):
        """ If ``transition`` fires we add the given priorities to the given places for the given location.

        :param transition: the transition that could fire
        :type transition: :class:`Transition <petrinet_simulator.Transition>`
        :param priority: for a given key place we associate a list of priority transitions
        :type priority: dict

        * options:

            * ``location = 'self'``: two kind of values possible:

            * ``'self'``: the given priority will be add to this token after the fire
            * ``(place, tokenName)``: All the token on ``place`` whose name contains ``tokenName`` will receive
                                      the given priority after the fire. Here 'contains' means that ``tokenName
                                      in self.name.split('_')``.

            * ``pref = 'time'``: the added priority will have this pref as option.
                                 See also :func:`addPriority <petrinet_simulator.Token.addPriority>`

        **Example:**

        >>> import petrinet_simulator as pns
        >>>
        >>> token1 = pns.Token(name = 'token1')
        >>> token2 = pns.Token(name = 'token2')
        >>> place1 = pns.Place(name = 'place1')
        >>> place2 = pns.Place(name = 'place2')
        >>> trans1 = pns.Transition(name = 'tr1')
        >>> trans2 = pns.Transition(name = 'tr2')
        >>>
        >>> place1.addToken(token1)
        >>>
        >>> token1.addPriorityAfterFire(trans1, {place1: [trans2]})
        >>> priority = {place2: [trans2,trans1], place1: [trans1]}
        >>> token1.addPriorityAfterFire(trans2, priority, location = (place2, 'token1'), pref='pref')
        >>>
        >>> token1.print_priority_after_fire() #doctest: +NORMALIZE_WHITESPACE
        # <Transition : tr1>: #
        #   self --> {<Place : place1>: [<Transition : tr2>](pref=time)} #
        # #
        # <Transition : tr2>: #
        #   (<Place : place2>, 'token1') --> {<Place : place2>: [<Transition : tr2>, <Transition : tr1>](pref=pref), <Place : place1>: [<Transition : tr1>](pref=pref)} #
        """
        if self.priorityAfterFire.get(transition) is None:
            self.priorityAfterFire.setdefault(transition, {location: {}})
        else:
            self.priorityAfterFire[transition].setdefault(location, {})
        for pl, transitions in priority.iteritems():
            self.priorityAfterFire[transition][location].setdefault(pl, {'priority': [], 'pref': pref})
            for t in transitions:
                self.priorityAfterFire[transition][location][pl]['priority'].append(t)

    def addFireHeritance(self, tokenName, place, transition):
        """ If ``transition`` fires, the tokens on ``place``, such that ``tokenName in token.name.split('_')``,
            change :attr:`fire <petrinet_simulator.Token.fire>` to ``True``

        :param tokenName: part of concerning token's name
        :type tokenName: str
        :param place: We consider only token on this place
        :type place: :class:`Place <petrinet_simulator.Place>`
        :param transition: The priorities are added if and only if transition fires
        :type transition: :class:`Transition <petrinet_simulator.Transition>`

        **Example:**

        >>> import petrinet_simulator as pns
        >>>
        >>> token1 = pns.Token(name = 'token1')
        >>> token2 = pns.Token(name = 'token2')
        >>> place1 = pns.Place(name = 'place1')
        >>> trans1 = pns.Transition(name = 'tr1')
        >>>
        >>> place1.addToken(token2)
        >>>
        >>> token1.addFireHeritance('token2', place1, trans1)
        >>>
        >>> token1.print_fire_heritance() #doctest: +NORMALIZE_WHITESPACE
        # <Transition : tr1> --> {<Place : place1>:[token2]} #
        """
        if self.fireHeritance.get(transition) is None:
            self.fireHeritance.setdefault(transition, {})
        if self.fireHeritance[transition].get(place) is None:
            self.fireHeritance[transition].setdefault(place, [])
        self.fireHeritance[transition][place].append(str(tokenName))

    def get_priority_value(self, place, transition):
        """ Compute a priority value for ``token``. Given two tokens, the one with the biggest priority_value is fired first
            if ``transition`` is not a priority for ``token`` on ``place``, we return 0

            :param place: *
            :type place: :class:`Place <Place.Place>`
            :param transition: *
            :type transition: :class:`Transition <Transition.Transition>`

            :returns: A float bigger or equal to 0
        """
        try:
            return (pref_func(0.0), pref_func(self.priority[place]['priority'].index(transition)))
        except:
            return (0.0, 0.0)

    def print_priority(self):
        """ Print the priorities of :attr:`priority <petrinet_simulator.Token.priority>`'s attribute
        """
        for place, attr in self.priority.iteritems():
            print '%s --> [%s](pref=%s)' % (repr(place), ', '.join(map(repr, attr['priority'])), str(attr['pref']))

    def print_priority_after_fire(self):
        """ Print the attribute :attr:`priorityAfterFire <petrinet_simulator.Token.priorityAfterFire>`
        """
        for tr, dct in self.priorityAfterFire.iteritems():
            st = '%s:\n' % repr(tr)
            for loc, priority in dct.iteritems():
                st += '  %s --> {' % str(loc)
                for pl, attr in priority.iteritems():
                    s = '%s --> [%s](pref=%s)' % (repr(pl), ', '.join(map(repr, attr['priority'])), str(attr['pref']))
                    st += s
                st += '}\n'
            print st

    def print_fire_heritance(self):
        """Print the attribute :attr:`fireHeritance <petrinet_simulator.Token.fireHeritance>`
        """
        for tr, heritance in self.fireHeritance.iteritems():
            print '%s --> {%s}' % (repr(tr), ', '.join(['%s:[%s]' % (repr(pl), ', '.join(tkns))
                                                        for pl, tkns in heritance.iteritems()]))

    def addFirstProperties(self, *tok_save):
        # create the token that has the properties of every previous token
        names = set()
        for t in tok_save:
            # we keep the intersection of each priority
            for p, attr in t.priority.iteritems():
                if attr['pref'] == 'priority':
                    del attr['priority'][0]
                    self.addPriority(p, attr['priority'], attr['pref'])
            # save the name of tokens
            names.update(t.name.split('_') if t.name != 'no name' and t.name != '' else [])
        self.name = '_'.join(names) or 'no name'

        if self.name == 'no name':
            for p, attr in self.priority.iteritems():
                if not attr['priority']:
                    del self.priority[p]
