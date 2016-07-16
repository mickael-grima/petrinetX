# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 14:54:37 2016

@author: Mickael Grima
"""

from Transition import Transition
from Place import Place


class Token:
    """This class represent a token.

    A token is an object that moves in the Petrinet. It stays on :class:`places <petrinet_simulator.Place>`
    and may change its place when a :class:`transition <petrinet_simulator.Transition>` fire

    The token object contains the necessary informations to know how to fire this token in the petrinet.
    It can have priority transitions or fire heritance to impose an order for the firing token.
    """

    def __init__(self, name='no name', show=True, fire=True):
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

    def __str__(self):
        return ', '.join(self.name.split('_'))

    def __repr__(self):
        return '<Token : %s>' % str(self)

    def copy(token):
        """Make a copy of a token

        :param token: token to copy
        :type token: :class:`Token <petrinet_simulator.Token>`

        :returns: An instance of the class :class:`Token <petrinet_simulator.Token>`

        .. Warning:: Transition and place are shared !
                 If the variable is not a token, the method
                 raise an exception
        """
        if not isinstance(token, Token):
            raise TypeError('Token expected, got a %s instead' % token.__class__.__name__)

        tok = Token(token.name, token.show, token.fire)
        for place, attr in token.priority.iteritems():
            tok.addPriority(place, attr['priority'], attr['pref'])
        for transition, dictionnary in token.priorityAfterFire.iteritems():
            for loc, prt in dictionnary.iteritems():
                tok.addPriorityAfterFire(transition, prt, loc)
        for transition, attr in token.fireHeritance.iteritems():
            for place, toks in attr.iteritems():
                for tk in toks:
                    tok.addFireHeritance(tk, place, transition)
        return tok

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


class TimeToken(Token):
    """This class represent a token with time. It herits from the parent class :class:`Token <petrinet_simulator.Token>`
    """
    def __init__(self, name='no name', show=True, fire=True):
        super(TimeToken, self).__init__(name=name, show=show, fire=fire)
        self.placeClocks = {}
        """ We save inside a place as key and associated to this place the time that the token will live on this place.
            We can add a place's clock using the method addPlaceClock()
        """
        self.transitionClocks = {}
        """ We save inside a transition as key and associated to this transition the time that the token will live
            on this transition. We can add a transition's clock using the method addTransitionClock()
        """
        self.pclock = 0.0
        """ It represents the time that the tokens lived on the current place on the TimedPetriNet during a simulation.
            It is reinitialized to 0.0 when the token change its current place
        """
        self.tclock = {}
        """ It represents the time that the tokens lived on the current transitions on the TimedPetriNet
            during a simulation. Only the transition that can fire this token are save inside
        """
        self.currentClock = 0.0
        """It represents how much time lived the token in the TimedPetriNet during a simulation
        """
        self.minimumStartingTime = {}
        """The token can't be fired by the given transition before the associated time
        """

    def copy(token):
        if not isinstance(token, TimeToken):
            raise TypeError('TimeToken expected, got a %s instead' % token.__class__.__name__)

        # The new token
        tok = TimeToken(token.name, token.show, token.fire)

        # adapte pclock
        tok.pclock = token.pclock

        # Adapte currentClock
        tok.currentClock = token.currentClock

        # Adapte placeClocks
        for place, clock in token.placeClocks.iteritems():
            tok.addPlaceClock(place, clock)

        # Adapte transitionClocks
        for transition, clock in token.transitionClocks.iteritems():
            tok.addTransitionClock(transition, clock)

        # adapte tclock
        for transition, clock in token.tclock.iteritems():
            tok.tclock.setdefault(transition, clock)

        # Adapte priority
        for place, attr in token.priority.iteritems():
            tok.addPriority(place, attr['priority'], attr['pref'])

        # adapte priorityAfterFire
        for transition, dct in token.priorityAfterFire.iteritems():
            for loc, prt in dct.iteritems():
                for pl, attr in prt.iteritems():
                    tok.addPriorityAfterFire(transition, {pl: attr['priority']}, location=loc, pref=attr['pref'])

        # adapte fireHeritance
        for transition, attr in token.fireHeritance.iteritems():
            for place, toks in attr.iteritems():
                for tk in toks:
                    tok.addFireHeritance(tk, place, transition)

        return tok

    def addPlaceClock(self, place, clock=None):
        """ Add a place Clock to ``place``.

        :param place: place where token would wait
        :type place: :class:`Place <petrinet_simulator.Place>`

        * options:

          * ``clock = None`` : the duration that the token would wait on ``place``.
            If None then we consider the place's :attr:`time <petrinet_simulator.Place.time>`.

        .. Note:: If a place's clock already exists for ``place``, we add ``clock`` only if its value is higher
        """
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)

        if self.placeClocks.get(place) is None:
            if clock is None:
                self.placeClocks.setdefault(place, place.getPlaceTime())
            else:
                self.placeClocks.setdefault(place, clock)
        else:
            if clock is None:
                t = place.getPlaceTime()
            if t > self.placeClocks[place]:
                self.placeClocks[place] = t
            else:
                if(clock > self.placeClocks[place]):
                    self.placeClocks[place] = clock

    def addTransitionClock(self, transition, clock=None):
        """Add a transition Clock to :attr:`transitionClocks <petrinet_simulator.TimeToken.transitionClocks>`.

        :param transition: transition where token would wait
        :type transition: :class:`Transition <petrinet_simulator.Transition>`

        * options:

          * ``clock = None`` : the duration that the token would wait on ``transition``.
            If None then we consider the transition's :attr:`time <petrinet_simulator.Transition.time>`.

        .. Note:: If a transition's clock already exists for ``transition``,
                  we add ``clock`` only if its value is higher
        """
        if not isinstance(transition, Transition):
            raise TypeError('Transition expected, got a %s instead' % transition.__class__.__name__)

        if self.transitionClocks.get(transition) is None:
            if clock is None:
                self.transitionClocks.setdefault(transition, transition.getTransitionTime())
            else:
                self.transitionClocks.setdefault(transition, clock)
        else:
            if clock is None:
                t = transition.getTransitionTime()
            if t > self.transitionClocks[transition]:
                self.transitionClocks[transition] = t
            else:
                if clock > self.transitionClocks[transition]:
                    self.transitionClocks[transition] = clock

    def addMinimumStartingTime(self, transition, time):
        """ If a time already exists for ``transition`` we replace it by the given time

        :param transition:
        :type transition: :class:`Transition <petrinet_simulator.Transition>`
        :param time:
        :type time: int, long or float

        .. Note:: If a transition's minimumStartingTime already exists for ``transition``,
                  we add ``time`` only if its value is higher
        """
        if not isinstance(time, int) and not isinstance(time, long) and not isinstance(time, float):
            raise TypeError('Int, long or float expected, got a %s instead' % time.__class__.__name__)
        if not isinstance(transition, Transition):
            print '**WARNING** transition argument is not a Transition object'
        if self.minimumStartingTime.get(transition) is None:
            if time is not None:
                self.minimumStartingTime.setdefault(transition, time)
            else:
                self.minimumStartingTime.setdefault(transition, transition.minimumStartingTime)
        else:
            mt = self.minimumStartingTime[transition]
            if time is not None:
                if time > mt:
                    self.minimumStartingTime[transition] = time
            else:
                if transition.minimumStartingTime > mt:
                    self.minimumStartingTime[transition] = transition.minimumStartingTime
