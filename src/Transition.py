# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 17:55:32 2016

@author: Mickael Grima
"""


class Transition(Node):
    """ This class represents a Transition in the class :class:`PetriNet <petrinet_simulator.PetriNet>`
        It is the class parent of class :class:`TimeTransition <petrinet_simulator.TimeTransition>`
        It herits from the parent class :class:`Node <petrinet_simulator.Node>`

        A transition can fire and have :class:`Token <petrinet_simulator.Token>`'s preferences
    """
    def __init__(self, name='no name', show=True):
        Node.__init__(self, name=name)
        self.show = show
        """ Boolean
            Can be:

              * ``True`` : This transition will be shown using the method
                           :func:`simulation <petrinet_simulator.TimedPetriNet.simulation>`
              * ``False`` : This transition won't be shown
        """
        self.tokenQueue = []
        """ List of token's lists. At each firing, only the first list is considered, then deleted after the firing.
            The transition can fire only if all the tokens given in the first list are on the places up and are enable.
        """
        self.tokenQueueAfterFire = []
        """ It's a List of dictionnary token's tuple: dictionnary. At each firing, only the first dictionnary is
            considered, then deleted after the firing.
            To a given tuple of token's name, we associate a dictionnary:
            :class:`Transition <petrinet_simulator.Transition>`: ``dict``. If all the tokens in the tuple are fired
            during the same firing, then for all transitions in the associated dictionnary, the associated tokenQueue
            is added to the previous transition.
            To each key ``transition`` is associated a dictionnary whose elements are:

                  * 'tokenQueue': tokenQueue
                  * 'presence_place': Boolean. If True after the firing we only add to the
                                      :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>` of ``transition``
                                      the token of places up whose names contain the string in :attr:`tokenQueue
                                      <petrinet_simulator.Transition.tokenQueue>`
                  * 'nb_tok': Int ot Long.

                  * If ``nb_tok = -1`` we add all the permitted token to the
                    :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>` of ``transition``
                  * else we add the indicated number of token
            """

    def __str__(self):
        return self.name

    def copy(transition):
        """Make a copy of ``transition``

        :param transition: transition to copy
        :type transition: :class:`Transition <petrinet_simulator.Transition>`

        :returns: An instance of the class :class:`Transition <petrinet_simulator.Transition>`
        """
        if not isinstance(transition, Transition):
            raise TypeError('Transition expected, got a %s instead' % transition.__class__.__name__)

        # Create the new transition
        tr = Transition(transition.name, transition.show)

        # Adapte tokenQueue
        for tkns in transition.tokenQueue:
            tr.insertTokenQueue(tkns)

        # Apdate tokenQueueAfterFire
        for i in range(len(transition.tokenQueueAfterFire)):
            dct = transition.tokenQueueAfterFire[i]
            for key, dc in dct.items():
                for t, attr in dc.items():
                    for tkns in attr['tokenQueue']:
                        tokenNames = []
                        for tkn in tkns:
                            tokenNames.append(tkn)
                        tr.insertTokenQueueAfterFire(tokenNames, t, key, i=i, place_presence=attr['place_presence'],
                                                     nb_tok=attr['nb_tok'])

        return tr

    def insertTokenQueue(self, *tokenNames, **options):
        """ Insert the given tokenNames to the transition's attribute
            :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>`

            :param tokenNames: token's name(s) to add to the tokenQueue
            :type tokenNames: *

            * options:

              * ``i = -1`` : The place where we insert the token's names(s)
                             There are many possible values:

                     * if ``i == -1`` or ``i == len(self.tokenQueue)`` we insert the token's name(s) at the end of
                       :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>`
                     * if ``i > len(self.tokenQueue)``, we raise a valueError
                     * else we add the token's name(s) at the place ``i`` in
                       :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>`

              * ``new_dct_tkn = False`` : A boolean.
                          If True we add a new list at the place ``i`` in
                          :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>`,
                          else we add the token's name(s) in the list at place ``i``.
                          Notice that if if ``i != -1 and i != len(self.tokenQueue)``, we add a new list at the end
                          of :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>` in any case

            .. Note:: tokenNames can have several types:

                      * *List*, *dict* or *tuple*: in this case we consider all the elements as below and we add them
                                                   at the right place
                      * anything else: We consider then the string conversion ``str(tokenNames)`` and we add it
                                       at the right place
        """
        i, new_dct_tkn = options['i'], options['new_dct_tkn']
        if not isinstance(i, int) and not isinstance(i, long):
            raise TypeError('Int or Long expected, got a %s instead' % i.__class__.__name__)
        if len(self.tokenQueue) < i:
            raise ValueError("token queue of transition %s has a length %s, we can't add a token to the place %s"
                             % (self.name, str(len(self.tokenQueue)), str(i)))

        if i == -1 or len(self.tokenQueue) == i:
            self.tokenQueue.append([])
            for tokenName in tokenNames:
                try:
                    self.tokenQueue[-1].append(str(tokenName))
                except:
                    print "TokeNames argument contains elements that can't be convert into a string"
            else:
                if new_dct_tkn:
                    self.tokenQueue.insert(i, [])
            for tokenName in tokenNames:
                try:
                    self.tokenQueue[i].append(str(tokenName))
                except:
                    print "TokeNames argument contains elements that can't be convert into a string"

    def insertTokenQueueAfterFire(self, tokenNames, transition, tkns, i=-1, j=-1, new_dct_tk_queue=False,
                                  new_dct_tkn=False, place_presence=False, nb_tok=-1):
        """ Insert to the key ``tkns`` and to the key ``transition`` the given token's name(s) to the transition's
            attribute :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueueAfterFire>`.

            :param tokenNames: token's name(s) to add
            :type tokenNames: *
            :param transition: We add ``tokenNames`` to tokenQueue associated at ``transition``
            :type transition: :class:`Transition <petrinet_simulator.Transition>`
            :param tkns: tuple of token's name(s)
            :type tkns: tuple

            * options:

              * ``i = -1`` : The place where we insert the token's names(s)
                     There are many possible values:

                     * if ``i == -1`` or ``i == len(self.tokenQueueAfterFire)`` we insert the token's name(s) at the end
                       of :attr:`tokenQueueAfterFire <petrinet_simulator.Transition.tokenQueueAfterFire>`
                     * if ``i > len(self.tokenQueueAfterFire)``, we raise a ``valueError``
                     * else we add the token's name(s) to the dictionnary at the place ``i`` in
                       :attr:`tokenQueueAfterFire <petrinet_simulator.Transition.tokenQueueAfterFire>`

              * ``j = -1`` : The place where we insert the token's names(s) in the ``tokenQueue`` associated to
                             ``transition``
                    There are many possible values: (let ``tokenQueueAfterFire[i][tkns][transition]`` be the tokenQueue
                    associated to ``transition``)

                     * if ``j == -1`` or ``j == len(tokenQueueAfterFire[i][tkns][transition])`` we insert the token's
                       name(s) at the end of ``tokenQueueAfterFire[i][tkns][transition]``
                     * if ``j > len(self.tokenQueueAfterFire)``, we raise a ``valueError``
                     * else we add the token's name(s) to the dictionnary at the place ``j`` in
                       tokenQueueAfterFire[i][tkns][transition]

              * ``new_dct_tkn = False`` : A boolean.
                          If True we add a new list at the place ``i`` in
                          :attr:`tokenQueueAfterFire <petrinet_simulator.Transition.tokenQueueAfterFire>`,
                          else we add the token's name(s) in the list at place ``i``.
                          Notice that if if ``i != -1 and i != len(self.tokenQueue)``, we add a new list at the end of
                          :attr:`tokenQueueAfterFire <petrinet_simulator.Transition.tokenQueueAfterFire>` in any case

              * ``new_dct_tk_queue = False`` : A boolean.
                           Let ``tokenQueueAfterFire[i][tkns][transition]`` be the tokenQueue associated to
                           ``transition``
                           If True we add a new list at the place ``j`` in ``tokenQueueAfterFire[i][tkns][transition]``,
                           else we add the token's name(s) in the list at place ``i``.
                           Notice that if ``i != -1 and i != len(self.tokenQueue)``, we add a new list at the end of
                           ``tokenQueueAfterFire[i][tkns][transition]`` in any case

              * ``place_presence = False`` : we associate it to the key ``place_presence``

              * ``nb_tok = -1`` : we associate it to the key ``nb_tok``

            .. Note:: tokenNames can have several types:

                      * *List*, *dict* or *tuple*: in this case we consider all the elements as below and we add them
                                                   at the right place
                      * anything else: We consider then the string conversion ``str(tokenNames)`` and we add it
                                       at the right place
        """
        if not isinstance(i, int) and not isinstance(i, long):
            raise TypeError('Int or Long expected, got a %s instead' % i.__class__.__name__)
        if not isinstance(j, int) and not isinstance(j, long):
            raise TypeError('Int or Long expected, got a %s instead' % j.__class__.__name__)
        if not isinstance(tkns, tuple):
            raise TypeError('Tuple expected, got a %s instead' % tkns.__class__.__name__)
        if len(self.tokenQueueAfterFire) < i:
            raise ValueError(
                "token queue after fire of transition %s has a length %s, we can't add a token to the place %s"
                % (self.name, str(len(self.tokenQueue)), str(i))
            )

        if i == -1 or len(self.tokenQueueAfterFire) == i:
            self.tokenQueueAfterFire.append({})
        else:
            if(new_dct_tk_queue):
                self.tokenQueueAfterFire.insert(i, {})

        if self.tokenQueueAfterFire[i].get(tkns) is None:
            self.tokenQueueAfterFire[i].setdefault(tkns, {})

        if self.tokenQueueAfterFire[i][tkns].get(transition) is not None:
            if(len(self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue']) < j):
                raise ValueError(
                    "token queue after fire of transition %s for transition %s has a length %s,"
                    "we can't add a token to the place %s"
                    % (self.name, transition.name, str(len(self.tokenQueueAfterFire[i][transition])), str(i))
                )
            
            if(isinstance(tokenNames, list) or isinstance(tokenNames, dict) or isinstance(tokenNames, tuple)):
            if(j == -1 or len(self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue']) == j):
                self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'].append([])
                for tokenName in tokenNames:
                try:
                    self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'][-1].append(str(tokenName))
                except:
                    print "TokeNames argument contains elements that can't be convert into a string"
            else:
                if(new_dct_tkn):
                self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'].insert(j, [])
                for tokenName in tokenNames:
                try:
                    self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'][j].append(str(tokenName))
                except:
                    print "TokeNames argument contains elements that can't be convert into a string"
            else:
            if(j == -1 or len(self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue']) == j):
                self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'].append([])
                try:
                self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'][-1].append(str(tokenNames))
                except:
                print "TokeNames argument can't be convert into a string"
            else:
                if(new_dct_tkn):
                self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'].insert(j, [])
                try:
                self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'][j].append(str(tokenNames))
                except:
                print "TokeNames argument can't be convert into a string"
        else:
            self.tokenQueueAfterFire[i][tkns].setdefault(transition, {'tokenQueue' : [[]], 'place_presence': place_presence, 'nb_tok': nb_tok})
            if(isinstance(tokenNames, list) or isinstance(tokenNames, dict) or isinstance(tokenNames, tuple)):
            for tokenName in tokenNames:
                try:
                self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'][-1].append(str(tokenName))
                except:
                print "TokeNames argument contains elements that can't be convert into a string"
            else:
            try:
                self.tokenQueueAfterFire[i][tkns][transition]['tokenQueue'][-1].append(str(tokenNames))
            except:
                print "TokeNames argument can't be convert into a string"



class TimeTransition(Transition, TimeNode):
    """This class represents a Transition with time in the class :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`
    It herits form both classes :class:`TimeNode <petrinet_simulator.TimeNode>` and :class:`Transition <petrinet_simulator.Transition>`
    
    This kind of transition has time's attribute
    """
    def __init__(self, name = '', time = 0.0, minimumStartingTime = -sys.maxint-1, show = True):
    Transition.__init__(self, name = name, show = show)
    TimeNode.__init__(self, name = name, time = time)
    self.minimumStartingTime = minimumStartingTime
    """Transition can NOT fire before this time
    """


    def copy(transition):
    if(not isinstance(transition, TimeTransition)):
        raise TypeError('Transition expected, got a ' + str(type(transition)).split(' ')[1].split("'")[1] + ' instead')
    
    tr = TimeTransition(transition.name, transition.time, transition.minimumStartingTime, transition.show)
    for tkns in transition.tokenQueue:
        tr.insertTokenQueue(tkns)
    for i in range(len(transition.tokenQueueAfterFire)):
        dct = transition.tokenQueueAfterFire[i]
        for key, dc in dct.items():
        for t, attr in dc.items():
            for tkns in attr['tokenQueue']:
            tokenNames = []
            for tkn in tkns:
                tokenNames.append(tkn)
            tr.insertTokenQueueAfterFire(tokenNames, t, key, i=i, place_presence= attr['place_presence'], nb_tok= attr['nb_tok'])
    return tr


    def getTransitionTime(self):
    """:returns: :attr:`time <petrinet_simulator.Transition.time>`
    """
    return self.time
