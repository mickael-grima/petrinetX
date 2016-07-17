# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
import scipy.stats as scs
import datetime as dt
import cvxopt as cvx
from Token import Token, TimeToken
from Place import Place, TimePlace
from Transition import Transition, TimeTransition


class PetriNet:
    """This class represents a petriNet
    """

    def __init__(self, name='no name'):
        self.name = name
        """ Name of the petriNet
        """
        self.places = {}
        """ Dictionnary of places to whose we associate a number that represents the order we add the place
            in the petriNet
        """
        self.transitions = {}
        """ Dictionnary of transitions to whose we associate a number that represents the order we add the transition
            in the petriNet
        """

        self.inputs = {}
        """ Dictionnary of ``place`` to whose we associate a dictionnary of transitions: number of tokens.
            If a ``transition`` and an associated ``nb`` belongs to this dictionnary, it means that the ``transition``
            has the ``place`` as input and the input needs ``nb`` tokens to be activated.
        """
        self.outputs = {}
        """ Dictionnary of ``place`` to whose we associate a dictionnary of transitions: number of tokensself.
            If a ``transition`` and an associated ``nb`` belongs to this dictionnary, it means that the ``transition``
            has the ``place`` as output and the output gives ``nb`` tokens to the place down.
        """
        self.upplaces = {}
        """ Dictionnary of ``transition`` to whose we associate a dictionnary of places: number of tokens.
            If a ``place`` and an associated ``nb`` belongs to this dictionnary, it means that the ``transition``
            has the ``place`` as input and the input needs ``nb`` tokens to be activated.
        """
        self.downplaces = {}
        """ Dictionnary of ``transition`` to whose we associate a dictionnary of places: number of tokens.
            If a ``place`` and an associated ``nb`` belongs to this dictionnary, it means that the ``transition``
            has the ``place`` as output and the output gives ``nb`` tokens to the place down.
        """
        self.token = {}
        """ Dictionnary of ``place`` to whose we associate ``nb``, the number of tokens that are on ``place``
        """

        self.initialState = {}
        """ In this dictionnary we save all the necessary informations thanks to the method
            :func:'setInitialState <petrinet_simulator.PetriNet.setInitialState>` in order to reinitialized the petriNet
            after a simulation.
        """

        self.posPlaces = {}
        """ Dictionnary of ``place`` to whose we associate ``pos`` the position of ``place`` in the graph build thanks
            to the method :func:`Tools.write_graph <petrinet_simulator.Tools.write_graph>`
        """
        self.posTransitions = {}
        """ Dictionnary of ``transition`` to whose we associate ``pos`` the position of ``transition`` in the graph
            build thanks to the method :func:`Tools.write_graph <petrinet_simulator.Tools.write_graph>`
        """
        self.paths = {}
        """ Dictionnary of tuple (``place``, ``transition``) (respectively (``transition``, ``place``)) to whose we
            associate the path of the edge between ``place`` and ``transition``. A path is a list of points that
            represent the angle of the edge. First point is the position of ``place`` (respectively ``transition``),
            last point is the position of ``transition`` (respectively ``place``).
        """

    def __repr__(self):
        return '<PetriNet : %s>' % self.name

    def __str__(self):
        return '%s: %s place(s), %s transition(s)' % (self.name, len(self.places), len(self.transitions))

    @staticmethod
    def copy(petriNet):
        """ Make a copy of ``petriNet`` using the methods :func:`copy('place') <petrinet_simulator.Place.copy>` and
            :func:`copy('transition') <petrinet_simulator.Transition.copy>`

            :param petriNet: The petriNet to copy
            :type petriNet: :class:`PetriNet <petrinet_simulator.PetriNet>`

            :returns: An instance of class :class:`PetriNet <petrinet_simulator.PetriNet>`
        """
        if not isinstance(petriNet, PetriNet):
            raise TypeError('PetriNet expected, got a %s instead' % petriNet.__class__.__name__)

        pn = PetriNet(petriNet.name)
        copy = {}
        # Copy places
        for p, k in petriNet.places.iteritems():
            pl = Place.copy(p)
            pn.addPlace(pl)
            copy.setdefault(p, pl)
        # copy transitions
        for t, c in petriNet.transitions.iteritems():
            tr = Transition.copy(t)
            pn.addTransition(tr)
            copy.setdefault(t, tr)
        for p, dct in petriNet.inputs.iteritems():
            for t, n in dct.iteritems():
                pn.addInput(copy[p], copy[t], n)
        for p, dct in petriNet.outputs.iteritems():
            for t, n in dct.iteritems():
                pn.addOutput(copy[p], copy[t], n)
        for p, n in petriNet.token.iteritems():
            pn.token.setdefault(copy[p], n)

        return pn

# -------------------------------------------------------
# --------------- building functions --------------------
# -------------------------------------------------------

    def addPlace(self, place, pos=(0.0, 0.0)):
        """ Add ``place`` to the petriNet's attribute :attr:`places <petrinet_simulator.PetriNet.places>`

            :param place: place to add to the PetriNet
            :type place: :class:`Place <petrinet_simulator.Place>`

            * options

              * ``pos = (0.0, 0.0)`` : We add ``pos`` with the key ``place`` to the petriNet's attribute
                                       :attr:`posPlaces <petrinet_simulator.PetriNet.posPlaces>`
        """
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)

        self.places.setdefault(place, len(self.places))
        self.posPlaces[place] = pos

    def addTransition(self, transition, pos=(0.0, 0.0)):
        """ Add ``transition`` to the petriNet's attribute :attr:`transitions <petrinet_simulator.PetriNet.transitions>`

            :param transition: transition to add to the PetriNet
            :type transition: :class:`Transition <petrinet_simulator.Transition>`

            * options

              * ``pos = (0.0, 0.0)`` : We add ``pos`` with the key ``transition`` to the petriNet's attribute
                                       :attr:`posTransitions <petrinet_simulator.PetriNet.posTransitions>`
        """
        if not isinstance(transition, Transition):
            raise TypeError('Transition expected, got a %s instead' % transition.__class__.__name__)

        self.transitions.setdefault(transition, len(self.transitions))
        self.posTransitions[transition] = pos

    def addToken(self, place, *tokens):
        """ Add the given tokens to ``place``

            :param place: the place where we add the tokens
            :type place: :class:`Place <petrinet_simulator.Place>`
            :param tokens: the token(s) to add to ``place``
            :type tokens: *

            .. Note:: ``tokens`` can have several types:

                    * *List*, *dict* or *tuple*: In this case we add all the objects in tokens following the rule below.
                    * :class:`TimeToken <petrinet_simulator.TimeToken>`: We add ``tokens`` to ``place``
                    * anything else: We transform ``tokens`` to a string using ``str()`` and we add the new token whose
                      name is ``str(tokens)``
        """
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)
        if self.places.get(place) is None:
            print "**WARNING** Try to add a token to the inexistant place %s" % place.name

        else:
            for token in tokens:
                if isinstance(token, Token):
                    tok = token
                    place.addToken(tok)
                    if self.token.get(place) is None:
                        self.token.setdefault(place, 1)
                    else:
                        self.token[place] += 1
                else:
                    print "Tokens argument contains a non-Token object that can't be convert to a token"

    def removeToken(self, place, tokens):
        """ Remove the given tokens from ``place``

            :param place: the place from where we remove the tokens
            :type place: :class:`Place <petrinet_simulator.Place>`
            :param tokens: the token(s) to remove from ``place``
            :type tokens: *

            .. Warning:: ``tokens`` can have several types:

                    * *List*, *dict* or *tuple*: In this case we remove all the objects in tokens following
                                                 the rule below.
                    * :class:`TimeToken <petrinet_simulator.TimeToken>`: We remove ``tokens`` from ``place``
                    * anything else: nothing happens
        """
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)
        if self.places.get(place) is None:
            print "**WARNING** Try to remove a token to the inexistant place %s" % place.name

        for tok in tokens:
            if isinstance(tok, Token):
                token = tok
                if token in place.token:
                    if self.token.get(place) is not None:
                        if self.token[place] > 1:
                            self.token[place] -= 1
                        else:
                            del self.token[place]
                    place.removeToken(token)
            else:
                print "Tokens argument contains a non-Token object that can't be convert to a token"

    def insertTokenQueue(self, transition, tokenNames, i=-1, new_dct_tkn=False, place_presence=False, nb_tok=-1):
        """ Insert the given tokenNames to the ``transition``'s attribute
            :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>`

            :param transition: Transition to whose we add the given token's name(s) to the
                               :attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>`
            :type transition: :class:`Transition <petrinet_simulator.Transition>`
            :param tokenNames: token's name(s) to add to the tokenQueue
            :type tokenNames: *

            * options:

                * ``i = -1`` : see the method :func:`insertTokenQueue <petrinet_simulator.Transition.insertTokenQueue>`

                * ``new_dct_tkn = False`` : see the method :func:`insertTokenQueue <petrinet_simulator.Transition.insertTokenQueue>`

                * ``place_presence = False`` : see the attribute :attr:`tokenQueueAfterFire <petrinet_simulator.Transition.tokenQueueAfterFire>`

                * ``nb_tok = -1`` : see the attribute :attr:`tokenQueueAfterFire <petrinet_simulator.Transition.tokenQueueAfterFire>`

            .. Note:: tokenNames can have several types:

                  * *List*, *dict* or *tuple*: in this case we consider all the elements as below and we add them
                                               at the right place
                  * anything else: We consider then the string conversion ``str(tokenNames)`` and we add it
                                   at the right place

            .. Warning:: ``nb_tok`` can only have value higher than -1
        """
        if not isinstance(new_dct_tkn, bool):
            raise TypeError('Boolean expected, got a %s instead' % new_dct_tkn.__class__.__name__)
        if not isinstance(place_presence, bool):
            raise TypeError('Place expected, got a %s instead' % place_presence.__class__.__name__)

        tokNames = []
        if isinstance(tokenNames, list):
            for tkn in tokenNames:
                try:
                    tokNames.append(str(tkn))
                except:
                    print "Tokens argument contains a non-String object that can't be convert to a string"
        elif isinstance(tokenNames, tuple):
            for tkn in tokenNames:
                try:
                    tokNames.append(str(tkn))
                except:
                    print "Tokens argument contains a non-String object that can't be convert to a string"
        elif isinstance(tokenNames, dict):
            for tkn in tokenNames:
                try:
                    tokNames.append(str(tkn))
                except:
                    print "Tokens argument contains a non-String object that can't be convert to a string"
            print "**WARNING** TokenNames argument is a dictionnary, so there is no particular order !"
        else:
            try:
                tokNames.append(str(tokenNames))
            except:
                print "Tokens argument is a non-String object that can't be convert to a string"

        if nb_tok > len(tokNames) or nb_tok < -1:
            raise ValueError('Try to add %s in tokenQueue of transition %s but the given queue has a length of %s'
                             % (str(nb_tok), transition.name, len(tokNames)))

        tkns, j = [], 0
        nbt = len(tokNames) if nb_tok == -1 else nb_tok
        if place_presence:
            if self.upplaces.get(transition) is not None:
                upplaces = {p: nb for p, nb in self.upplaces[transition].iteritems()}
            for p, nb in upplaces.iteritems():
                for tok in p.token:
                    tkn = tokenNames[j]
                    if tkn in tok.name.split('_'):
                        tkns.append(tkn)
                        j += 1
                    if j >= nbt:
                        break
                if j >= nbt:
                    break
                j += 1
        else:
            for j in range(nbt):
                tkns.append(tokNames[j])
                j += 1

        if j < nbt:
            transition.insertTokenQueue(tkns, i=i, new_dct_tkn=new_dct_tkn)

    def addInput(self, place, transition, tok=1, path=[]):
        """ Add an input between ``place`` and ``transition``.
            Attributes :attr:`upplaces <petrinet_simulator.PetriNet.upplaces>` and
            :attr:`inputs <petrinet_simulator.PetriNet.inputs>` are instanciated.

            :param place:
            :type place: :class:`Place <petrinet_simulator.Place>`
            :param transition:
            :type transition: :class:`Transition <petrinet_simulator.Transition>`

            * options:

              * ``tok = 1`` : Represents the number of token that can supports the created edge
              * ``path = []`` : Represents the path between ``place`` and ``transition``

            .. Note:: If the input already exists, no modification is done.
                  If ``place`` and/or ``transition`` doesn't exist(s) in the petriNet, they are added and the input
                  is then created
        """
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)
        if not isinstance(transition, Transition):
            raise TypeError('Transition expected, got a %s instead' % transition.__class__.__name__)
        if tok < 0:
            raise ValueError('negative number of token')

        if self.places.get(place) is None:
            self.addPlace(place)
        if self.transitions.get(transition) is None:
            self.addTransition(transition)

        if tok != 0:
            if self.inputs.get(place) is None:
                self.inputs.setdefault(place, {transition: tok})
            else:
                self.inputs[place].setdefault(transition, tok)

            if self.upplaces.get(transition) is None:
                self.upplaces.setdefault(transition, {place: tok})
            else:
                self.upplaces[transition].setdefault(place, tok)

            self.paths.setdefault((place, transition), path)

    def removeInput(self, place, transition):
        """ Remove the input between ``place`` and ``transition``.
            Attributes :attr:`upplaces <petrinet_simulator.PetriNet.upplaces>` and
            :attr:`inputs <petrinet_simulator.PetriNet.inputs>` are instanciated.

            :param place: *
            :type place: :class:`Place <petrinet_simulator.Place>`
            :param transition: *
            :type transition: :class:`Transition <petrinet_simulator.Transition>`

            .. Note:: If no input exists, no modification is done.
                  If ``place`` and/or ``transition`` doesn't exist(s) in the petriNet, no modification is done
        """
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)
        if not isinstance(transition, Transition):
            raise TypeError('Transition expected, got a %s instead' % transition.__class__.__name__)

        if self.inputs.get(place) is not None and self.inputs[place].get(transition) is not None:
            del self.inputs[place][transition]
            if len(self.inputs[place]) == 0:
                del self.inputs[place]
        if self.upplaces.get(transition) is not None and self.upplaces[transition].get(place) is not None:
            del self.upplaces[transition][place]
            if len(self.upplaces[transition]) == 0:
                del self.upplaces[transition]

        if self.paths.get((place, transition)) is not None:
            del self.paths[(place, transition)]

    def addOutput(self, place, transition, tok=1, path=[]):
        """ Add an output between ``place`` and ``transition``.
            Attributes :attr:`downplaces <petrinet_simulator.PetriNet.downplaces>` and
            :attr:`outputs <petrinet_simulator.PetriNet.outputs>` are instanciated.

            :param place:
            :type place: :class:`Place <petrinet_simulator.Place>`
            :param transition:
            :type transition: :class:`Transition <petrinet_simulator.Transition>`

            * options:

              * ``tok = 1`` : Represents the number of token that can supports the created edge
              * ``path = []`` : Represents the path between ``place`` and ``transition``

            .. Note:: If the output already exists, no modification is done.
                  If ``place`` and/or ``transition`` doesn't exist(s) in the petriNet, they are added and the output
                  is then created
        """
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)
        if not isinstance(transition, Transition):
            raise TypeError('Transition expected, got a %s instead' % transition.__class__.__name__)
        if tok < 0:
            raise ValueError('negative number of token')

        if self.places.get(place) is None:
            self.addPlace(place)
        if self.transitions.get(transition) is None:
            self.addTransition(transition)

        if tok != 0:
            if self.outputs.get(place) is None:
                self.outputs.setdefault(place, {transition: tok})
            else:
                self.outputs[place].setdefault(transition, tok)

            if self.downplaces.get(transition) is None:
                self.downplaces.setdefault(transition, {place: tok})
            else:
                self.downplaces[transition].setdefault(place, tok)

            self.paths.setdefault((transition, place), path)

    def removeOutput(self, place, transition):
        """ Remove an output between ``place`` and ``transition``.
            Attributes :attr:`downplaces <petrinet_simulator.PetriNet.downplaces>` and
            :attr:`outputs <petrinet_simulator.PetriNet.outputs>` are instanciated.

            :param place: *
            :type place: :class:`Place <petrinet_simulator.Place>`
            :param transition: *
            :type transition: :class:`Transition <petrinet_simulator.Transition>`

            * options:

              * ``tok = 1`` : Represents the number of token that can supports the created edge
              * ``path = []`` : Represents the path between ``place`` and ``transition``

            .. Note:: If no output exists, no modification is done.
                  If ``place`` and/or ``transition`` doesn't exist(s) in the petriNet, no modification is done
        """
        if not isinstance(place, Place):
            raise TypeError('Place expected, got a %s instead' % place.__class__.__name__)
        if not isinstance(transition, Transition):
            raise TypeError('Transition expected, got a %s instead' % transition.__class__.__name__)

        if self.outputs.get(place) is not None and self.outputs[place].get(transition) is not None:
            del self.outputs[place][transition]
            if len(self.outputs[place]) == 0:
                del self.outputs[place]
        if self.downplaces.get(transition) is not None and self.downplaces[j].get(place) is not None:
            del self.downplaces[transition][place]
            if len(self.downplaces[transition]) == 0:
                del self.downplaces[transition]

        if self.paths.get((transition, place)) is not None:
            del self.paths[(transition, place)]

    def savePlaces(self):
        """ Save place's informations into :attr:`initialState <petrinet_simulator.PetriNet.initialState>`
        """
        for p, k in self.places.iteritems():
            copy = [Token.copy(tok) for tok in p.token]
            self.initialState.setdefault(p, copy)

    def saveTransitions(self):
        """ Save transition's informations into :attr:`initialState <petrinet_simulator.PetriNet.initialState>`
        """
        for t, c in self.transitions.iteritems():
            if len(t.tokenQueue) != 0:
                self.initialState.setdefault(t, {})
                self.initialState[t].setdefault('tokenQueue', [])
            for tkns in t.tokenQueue:
                self.initialState[t]['tokenQueue'].append([])
                for tkn in tkns:
                    self.initialState[t]['tokenQueue'][-1].append(tkn)
            if len(t.tokenQueueAfterFire) != 0:
                self.initialState.setdefault(t, {})
                self.initialState[t].setdefault('tokenQueueAfterFire', [])
            for dct in t.tokenQueueAfterFire:
                self.initialState[t]['tokenQueueAfterFire'].append({})
                for tkns, dc in dct.iteritems():
                    self.initialState[t]['tokenQueueAfterFire'][-1].setdefault(tkns, {})
                    for tr, attr in dc.iteritems():
                        at = {'tokenQueue': [], 'place_presence': attr['place_presence'], 'nb_tok': attr['nb_tok']}
                        for tab in attr['tokenQueue']:
                            at['tokenQueue'].append([])
                            for tkn in tab:
                                at['tokenQueue'][-1].append(tkn)
                        self.initialState[t]['tokenQueueAfterFire'][-1][tkns].setdefault(tr, at)

    def setInitialState(self):
        """ Instanciate the attribute :attr:`initialState <petrinet_simulator.PetriNet.initialState>`
        """
        self.initialState = {}
        self.savePlaces()
        self.saveTransitions()

    def buildPetriNet(self, places, transitions, inputs, outputs, tokens={}):
        """ Build a petriNet from the given arguments

            :param places: Places to add in the petriNet
            :type places: List, dict or tuple
            :param transitions: Transitions to add in the petriNet
            :type transitions: List, dict or tuple
            :param inputs: Inputs to add in the petrinet.
            :type inputs: *
            :param outputs: Outputs to add in the petrinet.
            :type inputs: *

            * options:

              * ``tokens = {}``: Tokens to add in the petrinet. For each place has to be associated a list, dict or tuple of :class:`TimeToken <petrinet_simulator.TimeToken>`

            .. Note:: ``inputs`` and ``outputs`` can have several types:

                * *List* or *tuple*: In this case they are represented by a matrix whose range represents ``transitions`` and lines ``places``. The range j and the line i give the output or input between the transition whose associated number in :attr:`self.transitions <petrinet_simulator.PetriNet.transitions>` is j and ``place`` whose associated number in :attr:`self.places <petrinet_simulator.PetriNet.places>` is i.
                * *Dict*: In this case they must have the same form as :attr:`self.transitions <petrinet_simulator.PetriNet.transitions>` and :attr:`self.places <petrinet_simulator.PetriNet.places>`.

            **Example:**

            >>> import petrinet_simulator as pns
            >>> pt = pns.PetriNet(name = 'pt')
            >>>
            >>> pl1 = pns.Place(name = 'pl1')
            >>> pl2 = pns.Place(name = 'pl2')
            >>> pl = [pl1, pl2]
            >>>
            >>> tr1 = pns.Transition(name = 'tr1')
            >>> tr = [tr1]
            >>>
            >>> inputs = {pl1: {tr1: 1}}
            >>> outputs = {pl2: {tr1: 2}}
            >>>
            >>> tok1 = pns.Token(name = 'tok1')
            >>> tok2 = pns.Token(name = 'tok2')
            >>> tokens = {pl1: [tok1, tok2]}
            >>>
            >>> pt.buildPetriNet(pl, tr, inputs, outputs, tokens = tokens)
            >>> print pt #doctest: +NORMALIZE_WHITESPACE
            # pt, 2 place(s), 1 transition(s) #
            >>> print pt.places #doctest: +NORMALIZE_WHITESPACE
            # {<Place : pl1>: 0, <Place : pl2>: 1} #
            >>> print pt.transitions #doctest: +NORMALIZE_WHITESPACE
            # {<Transition : tr1>: 0} #
            >>> print pt.token #doctest: +NORMALIZE_WHITESPACE
            # {<Place : pl1>: 2} #
            >>> print pt.inputs #doctest: +NORMALIZE_WHITESPACE
            # {<Place : pl1>: {<Transition : tr1>: 1}} #
            >>> print pt.upplaces #doctest: +NORMALIZE_WHITESPACE
            # {<Transition : tr1>: {<Place : pl1>: 1}}#
            >>> print pt.outputs #doctest: +NORMALIZE_WHITESPACE
            # {<Place : pl2>: {<Transition : tr1>: 2}} #
            >>> print pt.downplaces #doctest: +NORMALIZE_WHITESPACE
            # {<Transition : tr1>: {<Place : pl2>: 2}} #
        """
        if not isinstance(tokens, dict):
            raise TypeError('Dict expected, got a %s instead', tokens.__class__.__name__)
        if not isinstance(inputs, dict) and not isinstance(inputs, list) and not isinstance(inputs, tuple):
            raise TypeError('Dict or List or Tuple expected, got a %s instead' % inputs.__class__.__name__)
        if not isinstance(outputs, dict) and not isinstance(outputs, list) and not isinstance(outputs, tuple):
            raise TypeError('Dict or List or Tuple expected, got a %s instead' % outputs.__class__.__name__)

        if isinstance(places, list) or isinstance(places, dict) or isinstance(places, tuple):
            for p in places:
                self.addPlace(p)
        else:
            self.addPlace(places)
        if isinstance(transitions, list) or isinstance(transitions, dict) or isinstance(transitions, tuple):
            for t in transitions:
                self.addTransition(t)
        else:
            self.addTransition(transitions)

        for p, k in self.places.iteritems():
            for t, c in self.transitions.iteritems():
                if isinstance(inputs, list) or isinstance(inputs, tuple):
                    if inputs[k][c] > 0:
                        self.addInput(p, t, inputs[k][c])
                else:
                    if inputs.get(p) is not None and inputs[p].get(t) is not None:
                        self.addInput(p, t, inputs[p][t])
                if isinstance(outputs, list) or isinstance(outputs, tuple):
                    if outputs[k][c] > 0:
                        self.addOutput(p, t, outputs[k][c])
                else:
                    if outputs.get(p) is not None and outputs[p].get(t) is not None:
                        self.addOutput(p, t, outputs[p][t])

        for p, toks in tokens.iteritems():
            if isinstance(toks, list) or isinstance(toks, dict) or isinstance(toks, tuple):
                for tok in toks:
                    self.addToken(p, tok)
            else:
                self.addToken(toks)

    def reinitialized(self):
        """ Reinitialized the petriNet from the petriNet's attribute
            :attr:`initialState <petrinet_simulator.PetriNet.initialState>`, first instanciated by method
            :func:`setInitialState <petrinet_simulator.PetriNet.setInitialState>`
        """
        if len(self.initialState) == 0:
            return
        for p, k in self.places.iteritems():
            copy = []
            for tok in p.token:
                copy.append(tok)
            for tok in copy:
                self.removeToken(p, tok)
            for tok in self.initialState[p]:
                self.addToken(p, tok)
        for t, c in self.transitions.iteritems():
            t.tokenQueue = []
            t.tokenQueueAfterFire = []
            if self.initialState.get(t) is not None:
                if self.initialState[t].get('tokenQueue') is not None:
                    t.tokenQueue = self.initialState[t]['tokenQueue']
                if self.initialState[t].get('tokenQueueAfterFire') is not None:
                    t.tokenQueueAfterFire = self.initialState[t]['tokenQueueAfterFire']
        self.initialState = {}

    # TODO add options to see oonly what we want to see
    def analyse_petrinet_state(self):
    """This method print the current state of the petriNet:
    
          * Which transition is blocked
          * Which transition is enable
          * Several other informations about the transitions
    """
    transition_blocked = {}
    
    for t,c in self.transitions.iteritems():
        tokenNames = None
        if(len(t.tokenQueue) != 0):
        tokenNames = []
        tokenNames.extend(t.tokenQueue[0])
        if(self.upplaces.get(t) is None):
        if(tokenNames is not None):
            transition_blocked.setdefault(t, {'no_upplaces': tokenNames})
        continue
        if(tokenNames is not None and len(tokenNames) == 0):
        transition_blocked.setdefault(t, {'empty_list_queue': True})
        continue
        upplaces = self.upplaces[t]
        b = False
        for p,nb in upplaces.iteritems():
        if(len(p.token) == 0):
            b = True
        if(b):
        continue
        for p,nb in upplaces.iteritems():
        n = 0
        for tok in p.token:
            if(tok.priority.get(p) is None or t in tok.priority[p]['priority']):
            n += 1
            if(tokenNames is not None):
                for i in range(len(tokenNames)):
                tkn = tokenNames[i]
                if(tkn in tok.name.split('_')):
                    del tokenNames[i]
                    break
        if(nb > n):
            if(transition_blocked.get(t) is None):
            transition_blocked.setdefault(t, {})
            transition_blocked[t].setdefault(p, nb - n)
        if(tokenNames is not None):
        if(transition_blocked.get(t) is None):
            transition_blocked.setdefault(t, {})
        transition_blocked[t].setdefault('expecting_tokens', tokenNames)
    
    ets = self.enabledTransitionsSet()
    
    if(len(ets) != 0):
        print 'The following transition are enable :'
    else:
        print 'No enable transitions'
    for t,c in ets.iteritems():
        print '  - '+t.name
    print ''
    
    if(len(transition_blocked) != 0):
        print 'The following transition are blocked :'
        print ''
    else:
        print 'No transitions blocked'
    for t, dct in transition_blocked.iteritems():
        print 'Transition '+t.name+' is blocked :'
        if(dct.get('no_upplaces') is not None):
        tokenNames = dct['no_upplaces']
        st = '  - no places up and '
        if(len(tokenNames) == 0):
            st += 'transition has an empty list as first token queue'
        else:
            st += 'transition is waiting for the following tokens: '
            for i in range(len(tokNames)):
            tkn = tokNames[i]
            if(i == 0):
                st += tkn
            else:
                st += ', '+tkn
        
        if(dct.get('empty_list_queue') is not None):
        print '  - transition has an empty list as first token queue'
        
        b= True
        for p, n in dct.iteritems():
        if(self.places.get(p) is not None):
            print '  - ' + str(n) + ' enable token(s) missing on place ' + p.name
            b = False
        
        if(transition_blocked.get('expecting_tokens') is not None):
        tokenNames = transition_blocked['expecting_tokens']
        if(b and len(tokenNames) != 0):
            st = '  - There are enough enable tokens up to the transition but transition is waiting for the missing following tokens : '
            for i in range(len(tokNames)):
            tkn = tokNames[i]
            if(i == 0):
                st += tkn
            else:
                st += ', '+tkn
        
        print '############################'
        

#########################################################
################# other functions ######################
########################################################
    
    def changeFireToken(self, place, token, ets):
    """Change the attribute :attr:`fire <petrinet_simulator.TimeToken.fire>` of ``token`` and adapte the enable transitions Set ``ets`` given by the method :func:`enabledTransitionsSet <petrinet_simulator.PetriNet.enabledTransitionsSet>`
    
    :param place: Place where ``token`` is located
    :type place: :class:`Place <petrinet_simulator.Place>`
    :param token: Token to modify
    :type token: :class:`TimeToken <petrinet_simulator.TimeToken>`
    :param ets: Enabled transition set build by the method :func:`enabledTransitionsSet <petrinet_simulator.PetriNet.enabledTransitionsSet>`
    :type ets: dict
    
    .. Warning:: ``token`` has to be on ``place``, otherwise an error is raised
    """
    if(not isinstance(place, Place)):
        raise TypeError('Place expected, got a ' + str(type(place)).split(' ')[1].split("'")[1] + ' instead')
    if(not isinstance(token, Token)):
        raise TypeError('Token expected, got a ' + str(type(token)).split(' ')[1].split("'")[1] + ' instead')
    
    i = 0
    for tok in place.token:
        if(tok == token):
        i += 1
    if(i == 0):
        raise ValueError('token '+token.name+' is not on the place '+place.name)
    
    b = token.fire
    if(b):
        token.fire = False
    else:
        token.fire = True
    
    if(self.inputs.get(place) is not None):
        for t,n in self.inputs[place].iteritems():
        if(t in ets and not self.isEnabled(t)):
            del ets[t]
        if(self.isEnabled(t)):
            ets.setdefault(t, self.transitions[t])
    
    
    def isEnabled(self, transition): 
    """Compute if ``transition`` can fire. A transition can fire if:
    
          * It exists in the PetriNet
          * It's an object of class :class:`Transition <petrinet_simulator.Transition>`
          * On each place up, there are enough token with the following properties:
          * ``transition`` belong to the priority list of the token
          * The token can fire
          * All the name in the first list of :attr:`transition.tokenQueue <petrinet_simulator.Transition.tokenQueue>` belongs at least to one of the enable token above.
    
    :param transition: *
    :type transition: :class:`Transition <petrinet_simulator.Transition>`
    
    :returns: True if ``transition`` is enable, else False
    """
    if(isinstance(transition, Transition)):
        if(self.transitions.get(transition) is None):
        print "**WARNING** Transition argument doesn't exist in the petriNet!"
        return False
        if(self.upplaces.get(transition) is None):
        return True
    else:
        print '**WARNING** Transition argument is not a Transition object !'
        return False
    
    #to be enable, transition has to be in one of the token's priority on every place
    tokName_save = []
    if(len(transition.tokenQueue) != 0):
        for tokn in transition.tokenQueue[0]:
        tokName_save.append(tokn)
    upplaces = self.upplaces[transition]
    for p,nb in upplaces.iteritems():
        toks = p.token
        b = False
        i = 0
        #are there enough token on each place up
        for tok in toks:
        if(tok.fire and (tok.priority.get(p) is None or transition == tok.priority[p]['priority'][0] or (tok.priority[p]['pref'] == 'time' and transition in tok.priority[p]['priority']))):
            words = tok.name.split('_')
            for j in range(len(tokName_save)):
            if(tokName_save[j] in words):
                del tokName_save[j]
                break
            i += 1
        if(i >= nb):
        b = True
        if(not b):
        return False
    if(len(tokName_save) != 0):
        return False
        
    return True


    #return a sequence of token with the right priority and the right number of token, sorted considering the tokens clocks
    def getEnableToken(self, place, transition):
    """Compute a list of token's that belong to ``place`` enable for ``transition``
       This list is sorted regarding the clock's and the minimumStartingTime of each token
       The first criteria to order the tokens is **the appartenance to transition.**:attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>`, the second is **the time**
       
       :param place: *
       :type place: :class:`Place <petrinet_simulator.Place>`
       :param transition: *
       :type transition: :class:`Transition <petrinet_simulator.Transition>`
       
       .. Warning:: If there is NO input between ``place`` and ``transition``, the method return an empty list
    """
    if(self.inputs.get(place) is None or self.inputs[place].get(transition) is None):
        print "**WARNING** Place argument has no input with transition argument !"
        return []
    
    nb = self.inputs[place][transition]
    tokens = []
    times = []
        
        i = 0
        #first we add the token that must be fired by transition
        if(len(transition.tokenQueue) != 0):
        toks_pr = []
        for tok in transition.tokenQueue[0]:
        toks_pr.append(tok)
        for tok in place.token:
        if(tok.priority.get(place) is not None and transition in tok.priority[place]['priority'] and tok.fire):
            words = tok.name.split('_')
            for k in range(len(toks_pr)):
            tkn = toks_pr[k]
            if(tkn in words):
                del toks_pr[k]
                tokens.append(tok)
                i += 1
                break
        if(len(toks_pr) != 0):
        raise StandardError('available transition '+transition.name+' has not the available tokens up')
    
    while(i < nb):
        #we search the token with the strongest priority
        ind = sys.maxint
        j = 0
        token = None
        for tok in place.token:
        if(not tok in tokens and tok.priority.get(place) is not None and transition in tok.priority[place]['priority'] and tok.fire):
            j += 1
            #find the most priority transition and save the token
            for tr in range(len(tok.priority[place]['priority'])):
            if(tok.priority[place]['priority'][tr] == transition):
                if(ind > tr):
                ind = tr
                token = tok   
        if(j == 0):
        break
        tokens.append(token)
        i += 1
    
    for tok in place.token:
        if(i == nb):
        break
        if(not tok in tokens and tok.fire):
        tokens.append(tok)
        i += 1
    
    if(i < nb):
        raise StandardError('no enough available token on the place '+place.name+" for the enabled transition "+transition.name)
    
    return tokens
    
    
    def enabledTransitionsSet(self):
    """Build the set of enabled transitions
    
    :returns: A dictionnary :class:`Transition <petrinet_simulator.Transition>`: int
    """
    result = {t: c for t,c in self.transitions.iteritems() if self.isEnabled(t)}
    return result
    
    
    def adapteEnabledTransitionsSet(self, transitions, ets):
    n = 0
    for t in transitions:
        if(t in ets and not self.isEnabled(t)):
        del ets[t]
        n += 1
        if(not t in ets and self.isEnabled(t)):
        ets.setdefault(t, self.transitions[t])
        n += 1
    return n
    
    
    def isBlocked(self):
    """Compute if the there still are enabled transitions or Note
    
    :returns: A boolean
    """
    for t,c in self.transitions.iteritems():
        if(self.isEnabled(t)):
        return False
    return True
    
    
    def isInStructuralConflict(self, transition1, transition2):
    """Check if ``transition1`` and ``transition2`` are in structural conflict, i.e. one token or more can be fired by both transitions
    
    :param transition1: *
    :type transition1: :class:`Transition <petrinet_simulator.Transition>`
    :param transition2: *
    :type transition2: :class:`Transition <petrinet_simulator.Transition>`
    
    :returns: A boolean
    """
    if(self.transitions.get(transition1) is None):
        return False
    if(self.transitions.get(transition2) is None):
        return False
        
    if(self.upplaces.get(transition1) is not None):
        for p,nb in self.upplaces[transition1].iteritems():
        if(self.upplaces.get(transition2) is not None and p in self.upplaces[transition2]):
            return True
    return False


    def isAllInStructuralConflict(self, transitions):
    """Check if each transition in ``transitions`` is not in structural conflict with an other one.
    
    :param transitions: *
    :type transitions: List, dict or tuple
    """
    for tr1 in transitions:
        for tr2 in transitions:
        if(tr1 != tr2 and self.isInStructuralConflict(tr1, tr2)):
            return True
    return False
        
        
    def isInBehavioralConflict(self, transition1, transition2):
    """Check if ``transition1`` and ``transition2`` are in behavioral conflict, i.e. both transitions are enable but there are not enough tokens on places up in order to activate both transitions
    
    :param transition1: *
    :type transition1: :class:`Transition <petrinet_simulator.Transition>`
    :param transition2: *
    :type transition2: :class:`Transition <petrinet_simulator.Transition>`
    
    :returns: A boolean
    """
    if(self.transitions.get(transition1) is None):
        return False
    if(self.transitions.get(transition2) is None):
        return False   
            
    b = True
    for p,nb in self.token.iteritems():
        b = b and nb >= (self.inputs[p][transition1]+self.inputs[p][transition2])
    return (not b and self.isEnabled(transition1) and self.isEnabled(transition2))
    
    
    def isAllInBehavioralConflict(self, transitions):
    """Check if each transition in ``transitions`` is not in behavioral conflict with an other one.
    
    :param transitions: *
    :type transitions: List, dict or tuple
    """
    for tr1 in transitions:
        for tr2 in transitions:
        if(tr1 != tr2 and self.isInBehavioralConflict(tr1, tr2)):
            return True
    return False

    
    def conflictPlaces(self, transition1, transition2):        
    """Compute the places that are shared by both ``transition1`` and ``transition2``
    
    :param transition1: *
    :type transition1: :class:`Transition <petrinet_simulator.Transition>`
    :param transition2: *
    :type transition2: :class:`Transition <petrinet_simulator.Transition>`
    
    :returns: Dictionnary :class:`Place <petrinet_simulator.Place>`: int
    """
    places = {}
    
    if(self.upplaces.get(transition1) is not None):
        for p1,nb1 in self.upplaces[transition1].iteritems():
        if(self.upplaces.get(transition2) is not None and p1 in self.upplaces[transition2]):
            places.setdefault(p1, nb1)
    
    return places
    
    
    def AllConflictPlaces(self, transitions):
    """Compute all the conflict places between each couple of transitions in ``transitions``
    
    :param transitions: *
    :type transitions: List, dict or tuple
    
    :returns: Dictionnary :class:`Place <petrinet_simulator.Place>`: int
    """
    places = {}        
    if(isinstance(transitions, list) or isinstance(transitions, dict) or isinstance(transitions, tuple)):
        for t1 in transitions:
        for t2 in transitions:
            places.update(self.conflictPlaces(t1, t2))
    return places
    
    
    def mostPriorityTransition(self, transitions):
    """For each transition in ``transitions``, we keep the one that has the biggest preference compute using the method :func:`pref <petrinet_simulator.PetriNet.pref>`
    
    :param transitions: *
    :type transitions: List, dict or tuple
    
    :returns: An object of class :class:`Transition <petrinet_simulator.Transition>` or None if no transition are found
    """
    pf = 0.0
    transition = None
    
    if(isinstance(transitions, list) or isinstance(transitions, dict) or isinstance(transitions, tuple)):
        for t in transitions:
        m = self.pref(t)
        if(pf <= m):
            pf = m
            transition = t
    else:
        if(isinstance(transitions, Transition)):
        transition = transitions
    
    return transition
    
    
    def pref(self, transition):
    """The preference of ``transition`` is computed following these steps:
          * We consider the tokens up to ``transition`` and enabled for ``transition`` using the method :func:`getEnableToken <petrinet_simulator.PetriNet.getEnableToken>`
          * For each token above we compute the position ``ind`` of ``transition`` in :attr:`token.priority <petrinet_simulator.Token.priority>`
          * We apply the method :func:`pref_func <petrinet_simulator.Tools.pref_func>` that compute a value for ``ind``
          * We sum all the given value and we return the average
    
    :param transition: *
    :type transition: :class:`Transition <petrinet_simulator.Transition>`
    
    :returns: A float
    """
    if(not isinstance(transition, Transition)):
        return -1.
    
    result = 0.0
    nb = 0
    if(self.upplaces.get(transition) is not None):
        for p,n in self.upplaces[transition].iteritems():
        tokens = self.getEnableToken(p, transition)
        for tok in tokens:
            if(tok.priority.get(p) is not None):
            ind = 0
            for tr in tok.priority[p]['priority']:
                if(tr == transition):
                result += Tools.pref_funct(ind)
                nb += 1
                ind += 1
    if(nb == 0):
        return 0.0
    else:
        result /= nb
        return result
        
    
#########################################################
################# representation functions ####################
########################################################
    
    def __adaptePetriNet(self, transition, ets):
    tok_save = []
        transitions_save = {}
        
        #save the previous token and remove the token that were fired
        if(self.upplaces.get(transition) is not None):
        for p,nb in self.upplaces[transition].iteritems():
        toks = self.getEnableToken(p, transition)
        for tok in toks:
            tok_save.append(tok)
            self.removeToken(p, tok)
        if(self.inputs.get(p) is not None):
            for t,n in self.inputs[p].iteritems():
            transitions_save.setdefault(t,n)
        
        #If a transition is not enabled anymore then its clock is reinitialized
        for t,c in transitions_save.iteritems():
            if(ets.get(t) is not None and not self.isEnabled(t)):
                del ets[t]
        
        #we remove the token of transition.tokenQueue
        if(len(transition.tokenQueue) != 0):
        del transition.tokenQueue[0]
    
    #We adapte the tokenQueue of targeted transitions
    if(len(transition.tokenQueueAfterFire) != 0):
        for tkk, dct in transition.tokenQueueAfterFire[0].iteritems():
        tkk_save = []
        for i in range(len(tkk)):
            tkk_save.append(tkk[i])
        #if all tokens in tkk are in the firing token, then we apply the token queue after fire
        for tok in tok_save:
            i = 0
            while(i < len(tkk_save)):
            tkn = tkk_save[i]
            if(tkn in tok.name.split('_')):
                del tkk_save[i]
                continue
            i += 1
        if(len(tkk_save) != 0):
            continue
        for tr, attr in dct.iteritems():
            for i in range(len(attr['tokenQueue'])):
            tokenNames = []
            for tkn in attr['tokenQueue'][i]:
                tokenNames.append(tkn)
            self.insertTokenQueue(tr, tokenNames, place_presence = attr['place_presence'], nb_tok = attr['nb_tok'])
        del transition.tokenQueueAfterFire[0]
        
        #create the token after the fire
        token = self.__tokenAfterFire(transition, ets, tok_save)
        
        transitions_save = {}
        #Add places after the transition that fired
        if(self.downplaces.get(transition) is not None):
        for p,n in self.downplaces[transition].iteritems():
        for i in range(n):
            tok = Token.copy(token)
            self.addToken(p, tok)
        if(self.inputs.get(p) is not None):
            for t,n in self.inputs[p].iteritems():
            transitions_save.setdefault(t,n)
    
    #If a transition is enabled we add it to ets
        for t,c in transitions_save.iteritems():
            if(ets.get(t) is None and self.isEnabled(t)):
                ets.setdefault(t, c)
    
    
    def __tokenAfterFire(self, transition, ets, tok_save):
    #create the token that has the properties of every previous token
    tok = Token()
    tok.name = ''
    for t in tok_save:
            #we keep the intersection of each priority
            for p,attr in t.priority.iteritems():
        if(attr['pref'] == 'priority'):
            del attr['priority'][0]
            tok.addPriority(p, attr['priority'], attr['pref'])
        #adapte the name of the token
        words = tok.name.split('_')
        if(t.name != 'no name' and t.name != ''):
        ws = t.name.split('_')
        for w in ws:
            if(not w in words):
            if(len(tok.name) == 0):
                tok.name += w
                continue
            tok.name +='_' + w
    if(tok.name == ''):
        tok.name = 'no name'
        for p,attr in tok.priority.iteritems():
        if(len(attr['priority']) == 0):
            del tok.priority[p]
    
    #priority after fire
    for t in tok_save:
        for tr, dic in t.priorityAfterFire.iteritems():
            if(tr == transition):
            for loc, prt in dic.iteritems():
            if(loc == 'self'):
                for pl, attr in prt.iteritems():
                tok.addPriority(pl, attr['priority'], pref = attr['pref'])
            else:
                for token in loc[0].token:
                words = token.name.split('_')
                if(loc[1] in words):
                    for pl, trs in prt.iteritems():
                    token.addPriority(pl, trs)
        else:
            for loc, prt in dic.iteritems():
            for pl, attr in prt.iteritems():
                tok.addPriorityAfterFire(tr, {pl: attr['priority']}, location= loc, pref= attr['pref'])
        if(t.fireHeritance.get(transition) is not None):
        for pl, ts in t.fireHeritance[transition].iteritems():
            for tt in pl.token:
            if(tt.name in ts):
                if(not tt.fire):
                self.changeFireToken(pl, tt, ets)
        
        return tok
    
    
    def computeFiringTransition(self, ets):
    """Among the given transitions in ``ets``, this method compute the next transition to fire regarding priority, preference and time (only for :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`)
    
    :param ets: set of enabled transitions
    :type ets: dict
    
    :returns: an object of class :class:`Transition <petrinet_simulator.Transition>`
    
    .. Note:: To create ets we can invoque the method :func:`enabledTransitionsSet <petrinet_simulator.PetriNet.enabledTransitionsSet>`
    """
        #if only one transition can fire
        if(len(ets) == 1):
        for t,c in ets.iteritems():
        return t
        
        #if no transition are in conflict
        if(not self.isAllInStructuralConflict(ets)):
            for t,c in ets.iteritems():
        return t
        
        transition = self.mostPriorityTransition(ets)
        
        #if no transition have the priority
        if(transition is None):
            for t,c in ets.iteritems():
        return t
        
        #return the most priority transition
        return transition


    def fire(self, transition, ets):
    """Execute the firing of ``transition``, adapte ``ets`` and all places and tokens in the PetriNet
    
    :param transition: transition that fired
    :type transition: :class:`Transition <petrinet_simulator.Transition>`
    :param ets: set of enabled transitions
    :type ets: dict
    
    .. Warning:: ``ets`` must contain only enable transitions, otherwise an Error can be raised
    """
    if(self.transitions.get(transition) is None):
        raise ValueError("Transition '"+transition.name + "' doesn't exist in PetriNet") 
    
    #adapte the places
    self.__adaptePetriNet(transition, ets)
    
    
    def oneFireSimulation(self, ets):
    """Compute the next firing transition and execute the firing: the two methods called are :func:`computeFiringTransition <petrinet_simulator.PetriNet.computeFiringTransition>` and :func:`fire <petrinet_simulator.PetriNet.fire>`
    
    :param ets: set of enabled transitions
    :type ets: dict
    
    :returns: an object of class :class:`Transition <petrinet_simulator.Transition>`
    """
    #compute the minimum of time for enabled transitions, and choose the transition
    transition = self.computeFiringTransition(ets)
    
    #fire and adapte each clocks
    self.fire(transition, ets)
    
    #we return the new token
    return transition


    def simulation(self, show = True, niter = float('nan')):
        if(not isinstance(show, bool)):
        raise TypeError('Boolean expected, got a ' + str(type(show)).split(' ')[1].split("'")[1] + ' instead')
        
        if(show):
        print 'beginning of the simulation'
        print ''
        
        if(self.initialState == {}):
        self.setInitialState()
        ets = self.enabledTransitionsSet()
        
        n = 0
    while(len(ets) != 0 and not n >= niter):
        transition = self.oneFireSimulation(ets)
        n += 1
        
        if(transition.show and show):
        print transition.name + ' fired'
        print ''
    
    if(show):
        print 'end of the simulation'
    
    
    #TODO to adapte, to document
    def reachabilityGraph(self, initialToken):
        graph = {}
        visited = {}
        queue = [initialToken]
        while(len(queue)>0):
            token = queue[0]
            visited.setdefault(tuple(token),token)
            queue.remove(token)
            ets = self.enabledTransitionsSet(token)
            neighbours = {}
            for t,c in ets.iteritems():
                tk = self.fire(t,token)
                neighbours.setdefault(t, tk)
                b = True
                for c,v in visited.iteritems():
                    b2 = False
                    for i in range(len(tk)):
                        if(tk[i] != v[i]):
                            b2=True
                    b = b and b2
                if(b == True):
                    queue.append(tk)
            graph.setdefault(tuple(token),neighbours)
        return graph
        


class TimedPetriNet(PetriNet):
    """This class herites from :class:`PetriNet <petrinet_simulator.PetriNet>`.
    
    The time is added, and simulations are also possible
    """
    #fields used in this class
    #
    #tclock -> dictionnary that repertory each clock whom the key is the associated transition
    #currentClock -> The current time
    #
    #for places: each token have to stay time on each place. A fire doesn't reinitialize the clock of a place
    #for transitions: if a transition fire, it reinitializes its own clock, but not the others.

#########################################################
################# constructor ##########################
########################################################

    def __init__(self, name = None, startDate = None, currentClock = 0.0):
        PetriNet.__init__(self, name)
        self.currentClock = currentClock
        self.startDate = startDate
    
    
    @staticmethod
    def copy(petriNet):
    if(not isinstance(petriNet, TimedPetriNet)):
        raise TypeError('TimedPetriNet expected, got a ' + str(type(petriNet)).split(' ')[1].split("'")[1] + ' instead')
    
    pn = TimedPetriNet(petriNet.name)
    copy = {}
    for p,k in petriNet.places.iteritems():
        pl = TimePlace.copy(p)
        pn.addPlace(pl)
        copy.setdefault(p, pl)
    for t,c in petriNet.transitions.iteritems():
        tr = TimeTransition.copy(t)
        pn.addTransition(tr)
        copy.setdefault(t, tr)
    #Make a copy of tokens
    for p,k in pn.places.iteritems():
        for tok in p.token:
        placeClocks = {}
        for pl,cl in tok.placeClocks.iteritems():
            placeClocks.setdefault(copy[pl], cl)
        tok.placeClocks = placeClocks
        ######
        transitionClocks = {}
        for tr,cl in tok.transitionClocks.iteritems():
            transitionClocks.setdefault(copy[tr], cl)
        tok.transitionClocks = transitionClocks
        ######
        tclock = {}
        for tr, cl in tok.tclock.iteritems():
            tclock.setdefault(copy[tr], cl)
        tok.tclock = tclock
        ######
        priority = {}
        for pl,attr in tok.priority.iteritems():
            priority.setdefault(copy[pl], {'priority': [], 'pref': attr['pref']})
            for tr in attr['priority']:
            priority[copy[pl]]['priority'].append(copy[tr])
        tok.priority = priority
        ######
        priorityAfterFire = {}
        for tr, dct in tok.priorityAfterFire.iteritems():
            priorityAfterFire.setdefault(copy[tr], {})
            for loc, prt in dct.iteritems():
            priorityAfterFire[copy[tr]].setdefault(loc, {})
            for pl,attr in prt.iteritems():
                priorityAfterFire[copy[tr]][loc].setdefault(copy[pl], {'priority': [], 'pref': attr['pref']})
                for t in attr['priority']:
                priorityAfterFire[copy[tr]][loc][copy[pl]]['priority'].append(copy[t])
        tok.priorityAfterFire = priorityAfterFire
        ######
        fireHeritance = {}
        for tr,dct in tok.fireHeritance.iteritems():
            fireHeritance.setdefault(copy[tr], {})
            for pl,toks in dct.iteritems():
            fireHeritance[copy[tr]].setdefault(copy[pl], [])
            for tokName in toks:
                fireHeritance[copy[tr]][copy[pl]].append(tokName)
        tok.fireHeritance = fireHeritance
    #Make a copy of transitions
    for t,c in pn.transitions.iteritems():
        tokenQueueAfterFire = []
        for dct in t.tokenQueueAfterFire:
        tokenQueueAfterFire.append({})
        for tkns, dc in dct.iteritems():
            tokenQueueAfterFire[-1].setdefault(tkns, {})
            for tr, attr in dc.iteritems():
            tokenQueueAfterFire[-1][tkns].setdefault(copy[tr], {'tokenQueue' : [], 'place_presence': attr['place_presence'], 'nb_tok': attr['nb_tok']})
            for tns in attr['tokenQueue']:
                tokenQueueAfterFire[-1][tkns][copy[tr]]['tokenQueue'].append([])
                for tn in tns:
                tokenQueueAfterFire[-1][tkns][copy[tr]]['tokenQueue'][-1].append(tn)
        t.tokenQueueAfterFire = tokenQueueAfterFire
    for p,dct in petriNet.inputs.iteritems():
        for t,n in dct.iteritems():
        pn.addInput(copy[p],copy[t],n)
    for p,dct in petriNet.outputs.iteritems():
        for t,n in dct.iteritems():
        pn.addOutput(copy[p],copy[t],n)
    for p,n in petriNet.token.iteritems():
        pn.token.setdefault(copy[p],n)
    
    pn.currentClock = petriNet.currentClock
    pn.startDate = petriNet.startDate
    
    return pn
    


#########################################################
################# building functions ###################
########################################################    
    
    def addToken(self, place, tokens):
    if(not isinstance(place, Place)):
        raise TypeError('Place expected, got a ' + str(type(place)).split(' ')[1].split("'")[1] + ' instead')
    if(self.places.get(place) is None):
        print "**WARNING** Try to add a token to the inexistant place "+place.name
    
    else:
        if(isinstance(tokens, list) or isinstance(tokens, dict) or isinstance(tokens, tuple)):
        for token in tokens:
            if(isinstance(token, Token)):
            tok = token
            else:
            try:
                tok = TimeToken(str(token))
            except:
                print "Tokens argument contains a non-Token object that can't be convert to a token"
            place.addToken(tok)
            if(self.inputs.get(place) is not None):
            for t,n in self.inputs[place].iteritems():
                tok.addTransitionClock(t, t.getTransitionTime())
                tok.tclock[t] = tok.transitionClocks[t]
                tok.addMinimumStartingTime(t, t.minimumStartingTime)
            if(self.token.get(place) is None):
            self.token.setdefault(place, 1)
            else:
            self.token[place] += 1
        else:
        if(isinstance(tokens, Token)):
            tok = tokens
        else:
            try:
            tok = TimeToken(str(tokens))
            except:
            print "Tokens argument contains a non-Token object that can't be convert to a token"
        place.addToken(tok)
        if(self.inputs.get(place) is not None):
            for t,n in self.inputs[place].iteritems():
            tok.addTransitionClock(t, t.getTransitionTime())
            tok.tclock[t] = tok.transitionClocks[t]
            tok.addMinimumStartingTime(t, t.minimumStartingTime)
        if(self.token.get(place) is None):
            self.token.setdefault(place, 1)
        else:
            self.token[place] += 1
    
    
    def savePlaces(self):
    for p,k in self.places.iteritems():
        copy = [TimeToken.copy(tok) for tok in p.token]
        self.initialState.setdefault(p, copy)
    
    
    def setInitialState(self):
    self.savePlaces()
    self.saveTransitions()
    self.initialState.setdefault('initialClock', self.currentClock)
    
    
    def reinitialized(self):
    if(len(self.initialState) == 0):
        return
    for p,k in self.places.iteritems():
        copy = []
        for tok in p.token:
        copy.append(tok)
        for tok in copy:
        self.removeToken(p,tok)
        for tok in self.initialState[p]:
        self.addToken(p, tok)
    for t,c in self.transitions.iteritems():
        t.tokenQueue = []
        t.tokenQueueAfterFire = []
        if(self.initialState.get(t) is not None):
        if(self.initialState[t].get('tokenQueue')):
            t.tokenQueue = self.initialState[t]['tokenQueue']
        if(self.initialState[t].get('tokenQueueAfterFire')):
            t.tokenQueueAfterFire = self.initialState[t]['tokenQueueAfterFire']
    self.currentClock = self.initialState['initialClock']
    self.initialState = {}


#########################################################
################# other functions ######################
########################################################

    def getEnableToken(self, place, transition):
    if(self.inputs.get(place) is None or self.inputs[place].get(transition) is None):
        print "**WARNING** Place argument has no input with transition argument !"
        return []
    
    nb = self.inputs[place][transition]
    tokens = []
    toks_sorted = {}
    times = []
    
    for tok in place.token:
        delta = tok.minimumStartingTime.get(transition, -sys.maxint-1) - self.currentClock
        if(delta < tok.pclock):
        time = tok.pclock
        else:
        time = delta
        time += tok.tclock[transition]
        if(time in toks_sorted):
        toks_sorted[time].append(tok)
        else:
        toks_sorted.setdefault(time, [tok])
        i, b = 0, False
        while(i < len(times)):
            if(times[i] > time):
            times.insert(i, time)
            b = True
            break
            i += 1
        if(not b or i == len(times)):
            times.append(time)
        
        i = 0
        #first we add the token that must be fired by transition
        if(len(transition.tokenQueue) != 0):
        toks_pr = []
        for tok in transition.tokenQueue[0]:
        toks_pr.append(tok)
        for time in times:
        tab = toks_sorted[time]
        for tok in tab:
            if(tok.priority.get(place) is not None and transition in tok.priority[place]['priority'] and tok.fire):
            words = tok.name.split('_')
            for k in range(len(toks_pr)):
                tkn = toks_pr[k]
                if(tkn in words):
                del toks_pr[k]
                tokens.append(tok)
                i += 1
                break
        #then we complete with the token with the minimal clock
        for time in times:
        tab = toks_sorted[time]
        while(i < nb):
            #we search the token with the strongest priority
            ind = sys.maxint
            j = 0
            token = None
            for tok in tab:
                if(not tok in tokens and tok.priority.get(place) is not None and transition in tok.priority[place]['priority'] and tok.fire):
                j += 1
                #find the most priority transition and save the token
                for tr in range(len(tok.priority[place]['priority'])):
                    if(tok.priority[place]['priority'][tr] == transition):
                        if(ind > tr):
                            ind = tr
                            token = tok     
        if(j == 0):
            break
        ind = 0
            for tok in tokens:
            if(token.pclock <= tok.pclock):
            break
            ind += 1
            tokens.insert(ind, token)
            i += 1
        if(i < nb):
            for tok in tab:
                if(tok.priority.get(place) is None and not tok in tokens and tok.fire):
                ind = 0
            for tk in tokens:
                if(tok.pclock <= tk.pclock):
                break
                ind += 1
                tokens.insert(ind,tok)
                i += 1
                if(i >= nb):
                break 
            if(i >= nb):
        break
    
    if(i < nb):
        raise StandardError('no enough available token on the place '+place.name+" for the enabled transition "+transition.name)
    
    return tokens
    
    
    def optimalTimeEts(self, ets, duration = sys.maxint):
    """Among the transitions in ``est``, compute the transition whose firing time is the minimal one.
    
    :param ets: set of enabled transitions
    :type ets: dict
    
    * options:
        * ``duration = sys.maxint``: if the minimal duration above is higher than ``duration``, then we return an empty list
    
    :returns: A list of objects :class:`Transition <petrinet_simulator.Transition>`
    """
        #compute the minimum of time for enabled transitions, and choose the transitions
    duration_ = sys.maxint
        transitions = []
        maxDuration = {}
        
        for t,c in ets.iteritems():
            mx = 0.0
            
            #for each t we compute the maximum time of the places before
            if(self.upplaces.get(t) is not None):
        for p,nb in self.upplaces[t].iteritems():
            toks = self.getEnableToken(p,t)
            delta = toks[-1].minimumStartingTime.get(t, -sys.maxint-1) - self.currentClock
            if(delta <= toks[-1].pclock):
            dt = toks[-1].pclock
            else:
            dt = delta
            dt += toks[-1].tclock[t]
            if(mx <= dt):
            mx = dt
            
            #we save the duration before the firing of transition t
            maxDuration.setdefault(t, mx)
            
            #duration before the first firing
            if(duration_ >= mx):
                duration_ = mx
        
        #we collect the transitions that can fire at the same minimal time duration
        for t,d in maxDuration.iteritems():
            if(d <= duration and d == duration_):
                transitions.append(t)
        
        return transitions, duration_
    
    
    def __adaptePetriNet(self, transition, duration, ets):
    tok_save = []
        transitions_save = {}
        
        #save the previous token and remove the token that were fired
        if(self.upplaces.get(transition) is not None):
        for p,nb in self.upplaces[transition].iteritems():
        toks = self.getEnableToken(p, transition)
        for tok in toks:
            tok_save.append(tok)
            self.removeToken(p, tok)
        if(self.inputs.get(p) is not None):
            for t,n in self.inputs[p].iteritems():
            transitions_save.setdefault(t,n)
        
        #If a transition is not enabled anymore then its clock is reinitialized
        for t,c in transitions_save.iteritems():
            if(ets.get(t) is not None and not self.isEnabled(t)):
                del ets[t]
        
        #we remove the token of transition.tokenQueue
        if(len(transition.tokenQueue) != 0):
        del transition.tokenQueue[0]
    
    #We adapte the tokenQueue of targeted transitions
    if(len(transition.tokenQueueAfterFire) != 0):
        for tkk, dct in transition.tokenQueueAfterFire[0].iteritems():
        tkk_save = []
        for i in range(len(tkk)):
            tkk_save.append(tkk[i])
        #if all tokens in tkk are in the firing token, then we apply the token queue after fire
        for tok in tok_save:
            i = 0
            while(i < len(tkk_save)):
            tkn = tkk_save[i]
            if(tkn in tok.name.split('_')):
                del tkk_save[i]
                continue
            i += 1
        if(len(tkk_save) != 0):
            continue
        for tr, attr in dct.iteritems():
            for i in range(len(attr['tokenQueue'])):
            tokenNames = []
            for tkn in attr['tokenQueue'][i]:
                tokenNames.append(tkn)
            self.insertTokenQueue(tr, tokenNames, place_presence = attr['place_presence'], nb_tok = attr['nb_tok'])
        del transition.tokenQueueAfterFire[0]
        
        transitions_save = {}
        #Adapte every place clocks
        for p,k in self.places.iteritems():
            for tok in p.token:
                if(tok.pclock <= duration):
            dur = duration - tok.pclock
                    tok.pclock = 0.0
                else:
            dur = 0.0
                    tok.pclock = tok.pclock - duration
                if(self.inputs.get(p) is not None):
            for t,n in self.inputs[p].iteritems():
            delta = tok.minimumStartingTime.get(t, -sys.maxint-1) - (self.currentClock + duration)
            if(delta > 0 and dur > delta):
                tok.tclock[t] -= dur - delta
                if(tok.tclock.get(t) < 0.0):
                tok.tclock[t] = 0.0
            if(delta <= 0.0):
                tok.tclock[t] -= dur
                if(tok.tclock.get(t) < 0.0):
                tok.tclock[t] = 0.0
        
        for p,n in self.upplaces.get(transition, {}).iteritems():
        for tok in p.token:
        tok.addTransitionClock(transition, transition.getTransitionTime())
        tok.tclock[transition] = tok.transitionClocks[transition]
        
        #create the token after the fire
        token = self.__tokenAfterFire(transition, ets, tok_save)
        
        #Add places after the transition that fired
        if(self.downplaces.get(transition) is not None):
        for p,n in self.downplaces[transition].iteritems():
        for i in range(n):
            tok = TimeToken.copy(token)
            self.addToken(p, tok)
        if(self.inputs.get(p) is not None):
            for t,n in self.inputs[p].iteritems():
            transitions_save.setdefault(t,n)
    
    #If a transition is enabled we add it to ets
        for t,c in transitions_save.iteritems():
            if(ets.get(t) is None and self.isEnabled(t)):
                ets.setdefault(t, c)
    
    
    def __tokenAfterFire(self, transition, ets, tok_save):
    #create the token that has the properties of every previous token
    tok = TimeToken()
    tok.name = ''
    for t in tok_save:
        #for each place we save the longest clock
        for p,c in t.placeClocks.iteritems():
            tok.addPlaceClock(p, c)
        #for each place we save the longest clock
        for tr,c in t.transitionClocks.iteritems():
            tok.addTransitionClock(tr, c)
            #we keep the intersection of each priority
            for p,attr in t.priority.iteritems():
        if(attr['pref'] == 'priority'):
            del attr['priority'][0]
            tok.addPriority(p, attr['priority'], attr['pref'])
        #adapte the name of the token
        words = tok.name.split('_')
        if(t.name != 'no name' and t.name != ''):
        ws = t.name.split('_')
        for w in ws:
            if(not w in words):
            if(len(tok.name) == 0):
                tok.name += w
                continue
            tok.name +='_' + w
    if(tok.name == ''):
        tok.name = 'no name'
        for p,attr in tok.priority.iteritems():
        if(len(attr['priority']) == 0):
            del tok.priority[p]
    
    #priority after fire
    for t in tok_save:
        for tr, dic in t.priorityAfterFire.iteritems():
            if(tr == transition):
                for loc, prt in dic.iteritems():
            if(loc == 'self'):
                for pl, attr in prt.iteritems():
                tok.addPriority(pl, attr['priority'], pref = attr['pref'])
            else:
                for token in loc[0].token:
                words = token.name.split('_')
                if(loc[1] in words):
                    for pl, attr in prt.iteritems():
                    token.addPriority(pl, attr['priority'], attr['pref'])
        else:
            for loc, prt in dic.iteritems():
            for pl, attr in prt.iteritems():
                tok.addPriorityAfterFire(tr, {pl: attr['priority']}, location= loc, pref= attr['pref'])
        if(t.fireHeritance.get(transition) is not None):
        for pl, ts in t.fireHeritance[transition].iteritems():
            for tt in pl.token:
            if(tt.name in ts):
                if(not tt.fire):
                self.changeFireToken(pl, tt, ets)
        
        return tok


#########################################################
################# dynamic functions ####################
########################################################
      
    def computeFiringTransition(self, ets, duration = sys.maxint):        
        if(len(ets) == 0):
            return None, 0.0
        
        #compute the enabled transitions with minimal firing time
        transitions, duration_ = self.optimalTimeEts(ets, duration)
        
        if(len(transitions) == 0):
        return None, duration_
        
        #if only one transition can fire
        if(len(transitions) == 1):
            return transitions[0], duration_
        
        #if no transition are in conflict
        if(not self.isAllInStructuralConflict(transitions)):
            return transitions[len(transitions)-1], duration_
        
        transition = self.mostPriorityTransition(transitions)
        
        #if no transition have the priority
        if(transition is None):
            return transitions[len(transitions)-1], duration_
        
        #return the most priority transition
        return transition, duration_


    def fire(self, transition, ets, duration = 0.0):
    if(self.transitions.get(transition) is None):
        raise ValueError("Transition '"+transition.name + "' doesn't exist in PetriNet") 
    
    #adapte the places
    self.__adaptePetriNet(transition, duration, ets)
    
    
    def oneFireSimulation(self, ets, duration = sys.maxint):  
    #compute the minimum of time for enabled transitions, and choose the transition
    transition, duration_ = self.computeFiringTransition(ets, duration)
    
    if(transition is None):
        return duration_, None
    
    #fire and adapte each clocks
    self.fire(transition, ets, duration_)
    
    #we return the new token and the duration
    return duration_, transition
        
        
    def simulation(self, show = True, step = None, niter = float('nan')):
    """Execute the simulation of the PetriNet. It invoques in a loop the method :func:`oneFireSimulation <petrinet_simulator.PetriNet.oneFireSimulation>`
    
    * options:
        
        * ``show = True``: if True, informations about firing transitions and currentclock are printed
        * ``step = None``: If a value is given, at each step we increase the currentclock of step, and we try to fire a transition. If it's None, we compute the next firing transition and then we increase the currentclock of the necessary amont of time
        * ``niter = nan``: If a value is done, we do only ``niter`` iterations, if nan we iterate until there are no enabled transitions anymore
    """
        if(not isinstance(show, bool)):
        raise TypeError('Boolean expected, got a ' + str(type(show)).split(' ')[1].split("'")[1] + ' instead')
    if(step is not None and not isinstance(step, int) and not isinstance(step, long) and not isinstance(step, float)):
        raise TypeError('Numaric value expected, got a ' + str(type(step)).split(' ')[1].split("'")[1] + ' instead')
        
        if(show):
        print 'beginning of the simulation'
        print 'currentTime : ',self.currentClock
        print ''
        
        if(self.initialState == {}):
        self.setInitialState()
        ets = self.enabledTransitionsSet()
        
        n = 0
        if(step is None):
        while(len(ets) != 0 and not n >= niter):
        duration, transition = self.oneFireSimulation(ets)
        
        n += 1
            
        self.currentClock += duration
        if(self.currentClock < transition.minimumStartingTime):
            raise ValueError('transition '+transition.name+' fired before his minimum starting time')
                    
        if(transition.show and show):
            print transition.name + ' fired'
            print 'currentTime : ',self.currentClock
            print ''
        
    else:
        duration = 0.0
        while(len(ets) != 0 and not n >= niter):
        b = True
        while(b):
            duration_, transition = self.oneFireSimulation(ets, duration)
            n += 1
            
            if(transition is None):
            b = False
            else:
            duration -= duration_
            if(transition.show and show):
                print transition.name + ' fired'
                print 'currentTime : ',self.currentClock
                print ''
            if(len(ets) == 0 or n >= niter):
                break
            
        if(len(ets) == 0 or n >= niter):
            break
        
        self.currentClock += step
        duration += step
    
    if(show):
        print self.currentClock
        print 'end of the simulation'



class Tools:
    """This class references some tools about Petrinets. It contains only static methods.
    """
  
    #lower is ind or clock, higher is the function
    @staticmethod
    def pref_funct(ind):
    """Higher ``ind`` is, lower the result is
    
    :param ind: *
    :type ind: int, long or float
    
    :returns: float
    """
    return 10.0/(1+ind)
    
    
    @staticmethod
    def concatenate(petriNet1, petriNet2, name = 'no name', input_connections = None, output_connections = None):
    """Build a global petriNet from the two given petrinets.
    
    :param petriNet1: *
    :type petriNet1: :class:`PetriNet <petrinet_simulator.PetriNet>`
    :param petriNet2: *
    :type petriNet2: :class:`PetriNet <petrinet_simulator.PetriNet>`
    
    * options:
    
        * ``name = 'no name'``: the name of the return petriNet
        * ``input_connections = None``: the input's connections added to the return petriNet. It's a tuple of place, transition
        * ``output_connections = None``: the output's connections added to the return petriNet. It's a tuple of place, transition
    
    :returns: an object of class :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`
    """
    if(not isinstance(petriNet1, PetriNet)):
        raise TypeError('PetriNet expected, got a ' + str(type(petriNet1)).split(' ')[1].split("'")[1] + ' instead')
    if(not isinstance(petriNet2, PetriNet)):
        raise TypeError('PetriNet expected, got a ' + str(type(petriNet2)).split(' ')[1].split("'")[1] + ' instead')
    
    minimumDate = None
    if(petriNet1.startDate is not None):
        if(petriNet2.startDate is not None):
        dur = (petriNet1.startDate - petriNet2.startDate).total_seconds()/60.
        if(dur > 0):
            minimumDate = petriNet2.startDate
        else:
            minimumDate = petriNet1.startDate
        else:
        minimumDate = petriNet1.startDate
    else:
        if(petriNet2.startDate is not None):
        minimumDate = petriNet2.startDate

    result = TimedPetriNet(str(name), startDate = minimumDate)
    
    #add the places and tokens
    for p1, k1 in petriNet1.places.iteritems():
        result.addPlace(p1)
    for p2, k2 in petriNet2.places.iteritems():
        result.addPlace(p2)
    
    #add tokens
    result.token.update(petriNet1.token)
    result.token.update(petriNet2.token)
    
    #add the transitions
    for t1, c1 in petriNet1.transitions.iteritems():
        result.addTransition(t1)
    for t2, c2 in petriNet2.transitions.iteritems():
        result.addTransition(t2)
    
    #create the inputs
    result.inputs.update(petriNet1.inputs)
    result.inputs.update(petriNet2.inputs)
    result.outputs.update(petriNet1.outputs)
    result.outputs.update(petriNet2.outputs)
    result.upplaces.update(petriNet1.upplaces)
    result.upplaces.update(petriNet2.upplaces)
    result.downplaces.update(petriNet1.downplaces)
    result.downplaces.update(petriNet2.downplaces)       
    
    #add the input_connections and output_connections
    if(input_connections is not None):
        for t in input_connections:
        result.addInput(t[0], t[1])
    if(output_connections is not None):    
        for t in output_connections:
        result.addOutput(t[0], t[1]) 
    
    return result

    
    @staticmethod
    def read_graph(src):
    """For a given ``src``, make a petriNet. ``src`` has to come from a document whose extension is graphml. The places in ``src`` have to be nodes with ellipse form, and the transitions nodes with rectangle form.
    
    :param src:
    :type src: docfile
    
    :returns: An object of class :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`
    """
    lines = src.readlines()
    
    while(True):
        line = lines[0]
        data = line.split(" ")
        if(data[2] == "<graph"):
        break
        else:
        del lines[0]
    
    pt = TimedPetriNet()
    nodes = []
    edges = []
    
    i = 0
    while(i < len(lines)):
        line = lines[i].rstrip('\n')
        data = line.split(" ")
        
        if("<node" in data and not 'yfiles.foldertype="group">' in data):
        
        end_node = ""
        j = 0
        word = data[j]
        while(word == ''):
            end_node += ' '
            j += 1
            word = data[j]
        end_node += "</node>\n"
        
        #### if the node a simple node is ####
        lines_node = []
        while(lines[i] != end_node):
            lines_node.append(lines[i].rstrip('\n'))
            i += 1
        lines_node.append(lines[i].rstrip('\n'))
        
        nodes.append(lines_node)
        
        if("<edge" in data):
        
        end_edge = ''
        j = 0
        word = data[j]
        while(word == ''):
            end_edge += ' '
            j += 1
            word = data[j]
        end_edge += "</edge>\n"
        
        #### if the node a simple node is ####
        lines_edge = []
        while(lines[i] != end_edge):
            lines_edge.append(lines[i].rstrip('\n'))
            i += 1
        lines_edge.append(lines[i].rstrip('\n'))
        
        edges.append(lines_edge)
        
        i += 1
    
    for lines in nodes:
        node, typ, pos = __create_node(lines)
        if(typ == "transition"):
        pt.addTransition(node, pos=pos)
        if(typ == "place"):
        pt.addPlace(node, pos=pos)
    
    for lines in edges:
        idd1, idd2, path = __create_edge(lines)
        for p,k in pt.places.iteritems():
        if(p.idd == idd1):
            place = p
            typ = 'input'
        if(p.idd == idd2):
            place = p
            typ = 'output'
        for t,c in pt.transitions.iteritems():
        if(t.idd == idd1 or t.idd == idd2):
            transition = t
        
        if(typ == 'input'):
        pt.addInput(place,transition, path = path)
        if(typ == 'output'):
        pt.addOutput(place, transition, path = path)
    
    return pt

    
    @staticmethod
    def __create_node(lines):
    
    name = None
    nb_tok = 0
    
    typ = None
    node = None
    
    line = lines[0].rstrip('\n')
    data = line.split(' ')
    i = 0
    while(data[i] != "<node"):
        i += 1
    word = data[i+1].split('=')[1].rstrip('>')
    idd = word.split('"')[1]
    
    i = 0
    while(i < len(lines)):
        
        line = lines[i].rstrip('\n')
        data = line.split(' ')
        
        if('<data' in data):
        
        #find the end of data
        end_data = ''
        j = 0
        word = data[j]
        while(word == ''):
            end_data += ' '
            j += 1
            word = data[j]
        end_data += "</data>"
        
        #explore data
        while(lines[i] != end_data):
            i += 1
            line = lines[i].rstrip('\n')
            dt = line.split('y:')
            
            #if it is a label
            if(len(dt) > 1 and dt[1].split(' ')[0] == "NodeLabel"):
            label = dt[1].rstrip("</").split('>')[1]
            if(label != ''):
                if(len(label) >= 3):
                name = label
                else:
                nb_tok = int(label)
            
            #transition or Place?
            if(len(dt) > 1 and dt[1].split(' ')[0] == "Shape"):
            shape = dt[1].split(' ')[1].rstrip('/>').split('=')[1]
            if(shape == '"ellipse"'):
                node = TimePlace()
                typ = 'place'
            if(shape == '"rectangle"'):
                node = TimeTransition()
                typ = 'transition'
            
            #transition or Place?
            if(len(dt) > 1 and dt[1].split(' ')[0] == "Geometry"):
            words = dt[1].split(' ')
            j = 0
            while(j < len(words)):
                w = words[j].rstrip('/>').split('=')
                if('x' in w):
                x = float(w[1].split('"')[1])
                if('y' in w):
                y = float(w[1].split('"')[1])
                j += 1
        
        i += 1
                
    if(typ == 'place'):
        node.name = name
        for i in range(nb_tok):
        tok = TimeToken()
        node.addToken(tok)
    if(typ == 'transition'):
        node.name = name
    if(typ is None):
        raise ValueError('this node is not a real node')
    
    node.idd = idd
    pos = (x,y)
    
    return node, typ, pos
    
    
    @staticmethod
    def __create_edge(lines):
    path = []

    line = lines[0].rstrip('\n')
    data = line.split(' ')
    i = 0
    while(data[i] == ''):
        i += 1
    
    idd1 = data[i+2].split('=')[1].split('"')[1]
    idd2 = data[i+3].split('=')[1].split('"')[1]
    
    i = 0
    while(i < len(lines)):
        line = lines[i].rstrip('\n')
        data = line.split('y:')
        dt = line.split(' ')
        
        if(len(data) > 1 and data[1].split(' ')[0] == 'Path'):
        
        #find the end of data
        end_path = ''
        j = 0
        word = dt[j]
        while(word == ''):
            end_path += ' '
            j += 1
            word = dt[j]
        end_path += "</y:Path>"
        i += 1
        
        while(lines[i] != end_path and lines[i].split(' ')[j] == ''):
            words = lines[i].rstrip('\n').split('y:')
            if(words[1].split(' ')[0] == 'Point'):
            w = words[1].rstrip('/>').split(' ')
            x = float(w[1].split('=')[1].split('"')[1])
            y = float(w[2].split('=')[1].split('"')[1])
            path.append((x,y))
            i += 1
        
        i += 1
    
    return idd1, idd2, path

    
    @staticmethod
    def write_graph(pt, direction):
    """From a given petriNet ``pt``, it makes a document saved to the given ``direction``, and write it in the graphml format.
    
    :param pt: *
    :type pt: :class:`PetriNet <petrinet_simulator.PetriNet>`
    :param direction: *
    :type direction: String
    
    .. Warning:: Places and Transitions in ``pt`` must have idd. Otherwise the nodes won't be created.
    """
    doc = open(direction,"w")
    
    doc.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    doc.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:java="http://www.yworks.com/xml/yfiles-common/1.0/java" xmlns:sys="http://www.yworks.com/xml/yfiles-common/markup/primitives/2.0" xmlns:x="http://www.yworks.com/xml/yfiles-common/markup/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:y="http://www.yworks.com/xml/graphml" xmlns:yed="http://www.yworks.com/xml/yed/3" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd">\n')
    doc.write('  <!--Created by yEd 3.14.1-->\n')
    doc.write('  <key attr.name="Description" attr.type="string" for="graph" id="d0"/>\n')
    doc.write('  <key for="port" id="d1" yfiles.type="portgraphics"/>\n')
    doc.write('  <key for="port" id="d2" yfiles.type="portgeometry"/>\n')
    doc.write('  <key for="port" id="d3" yfiles.type="portuserdata"/>\n')
    doc.write('  <key attr.name="url" attr.type="string" for="node" id="d4"/>\n')
    doc.write('  <key attr.name="description" attr.type="string" for="node" id="d5"/>\n')
    doc.write('  <key for="node" id="d6" yfiles.type="nodegraphics"/>\n')
    doc.write('  <key for="graphml" id="d7" yfiles.type="resources"/>\n')
    doc.write('  <key attr.name="url" attr.type="string" for="edge" id="d8"/>\n')
    doc.write('  <key attr.name="description" attr.type="string" for="edge" id="d9"/>\n')
    doc.write('  <key for="edge" id="d10" yfiles.type="edgegraphics"/>\n')
    doc.write('  <graph edgedefault="directed" id="G">\n')
    doc.write('    <data key="d0"/>\n')
    
    for p,k in pt.places.iteritems():
        Tools.__write_node(doc, p, 'place', k, pt.posPlaces[p])
        
    nb = len(pt.places)
    for t,c in pt.transitions.iteritems():
        Tools.__write_node(doc, t, 'transition', nb + c, pt.posTransitions[t])
    
    i = 0
    for p,dct in pt.inputs.iteritems():
        for t,nb in dct.iteritems():
        k = pt.places[p]
        c = pt.transitions[t]
        Tools.__write_edge(doc, i, k, nb + c, pt.paths[(p,t)])
        i += 1
    for p,dct in pt.outputs.iteritems():
        for t,nb in dct.iteritems():
        k = pt.places[p]
        c = pt.transitions[t]
        Tools.__write_edge(doc, i, nb + c, k, pt.paths[(p,t)])
        i += 1
    
    doc.write('  </graph>\n')
    doc.write('  <data key="d7">\n')
    doc.write('    <y:Resources/>\n')
    doc.write('  </data>\n')
    doc.write('</graphml>')
    
    doc.close()

    
    @staticmethod
    def __write_node(doc, node, typ, idd, pos):
    doc.write('    <node id="n'+str(idd)+'">\n')
    doc.write('      <data key="d5"/>\n')
    doc.write('      <data key="d6">\n')
    doc.write('        <y:ShapeNode>\n')
    doc.write('          <y:Geometry height="30.0" width="30.0" x="'+str(pos[0])+'" y="'+str(pos[1])+'"/>\n')
    
    if(typ == 'place' and len(node.token) > 0):    
        doc.write('          <y:Fill color="#FF6600" transparent="false"/>\n')
    else:
        doc.write('          <y:Fill color="#FFCC00" transparent="false"/>\n')
    
    doc.write('          <y:BorderStyle color="#000000" type="line" width="1.0"/>\n')
    
    if(node.time > 0):
        doc.write('          <y:NodeLabel alignment="center" autoSizePolicy="content" fontFamily="Dialog" fontSize="12" fontStyle="plain" hasBackgroundColor="false" hasLineColor="false" height="18.701171875" modelName="custom" textColor="#000000" visible="false" width="50.359375" x="-10.1796875" y="5.6494140625">time='+str(node.time)+'<y:LabelModel>\n')
        doc.write('              <y:SmartNodeLabelModel distance="4.0"/>\n')
        doc.write('            </y:LabelModel>\n')
        doc.write('            <y:ModelParameter>\n')
        doc.write('              <y:SmartNodeLabelModelParameter labelRatioX="0.0" labelRatioY="0.0" nodeRatioX="0.0" nodeRatioY="0.0" offsetX="0.0" offsetY="0.0" upX="0.0" upY="-1.0"/>\n')
        doc.write('            </y:ModelParameter>\n')
        doc.write('          </y:NodeLabel>\n')
    
    if(node.name != 'no name' and node.name is not None):
        doc.write('          <y:NodeLabel alignment="center" autoSizePolicy="content" fontFamily="Dialog" fontSize="30" fontStyle="plain" hasBackgroundColor="false" hasLineColor="false" height="40.7529296875" modelName="eight_pos" modelPosition="s" textColor="#000000" visible="true" width="185.787109375" x="-62.8935546875" y="64.0">'+node.name+'</y:NodeLabel>\n')
    
    if(typ == 'place' and len(node.token) > 0):
        doc.write('          <y:NodeLabel alignment="center" autoSizePolicy="content" fontFamily="Dialog" fontSize="20" fontStyle="plain" hasBackgroundColor="false" hasLineColor="false" height="40.7529296875" modelName="custom" textColor="#000000" visible="true" width="37.369140625" x="11.3154296875" y="9.62353515625">'+str(len(node.token))+'<y:LabelModel>\n')
    else:
        doc.write('          <y:NodeLabel alignment="center" autoSizePolicy="content" fontFamily="Dialog" fontSize="12" fontStyle="plain" hasBackgroundColor="false" hasLineColor="false" hasText="false" height="4.0" modelName="custom" textColor="#000000" visible="true" width="4.0" x="13.0" y="13.0">\n')
        doc.write('            <y:LabelModel>\n')
    
    doc.write('              <y:SmartNodeLabelModel distance="4.0"/>\n')
    doc.write('            </y:LabelModel>\n')
    doc.write('            <y:ModelParameter>\n')
    doc.write('              <y:SmartNodeLabelModelParameter labelRatioX="0.0" labelRatioY="0.0" nodeRatioX="0.0" nodeRatioY="0.0" offsetX="0.0" offsetY="0.0" upX="0.0" upY="-1.0"/>\n')
    doc.write('            </y:ModelParameter>\n')
    doc.write('          </y:NodeLabel>\n')
    
    if(typ == 'place'):
        doc.write('          <y:Shape type="ellipse"/>\n')
    if(typ == 'transition'):
        doc.write('          <y:Shape type="rectangle"/>\n')
    
    doc.write('        </y:ShapeNode>\n')
    doc.write('      </data>\n')
    doc.write('    </node>\n')

    
    @staticmethod
    def __write_edge(doc, idd, idd_source, idd_target, path):
    doc.write('    <edge id="e'+str(idd)+'" source="n'+str(idd_source)+'" target="n'+str(idd_target)+'">\n')
    doc.write('      <data key="d9"/>\n')
    doc.write('      <data key="d10">\n')
    doc.write('        <y:PolyLineEdge>\n')
    
    if(path == []):    
        doc.write('          <y:Path sx="0.0" sy="0.0" tx="0.0" ty="0.0"/>\n')
    else:
        doc.write('          <y:Path sx="0.0" sy="0.0" tx="0.0" ty="0.0">\n')
        for p in path:
        doc.write('            <y:Point x="'+str(p[0])+'" y="'+str(p[1])+'"/>\n')
        doc.write('          </y:Path>\n')
    
    doc.write('          <y:LineStyle color="#000000" type="line" width="1.0"/>\n')
    doc.write('          <y:Arrows source="none" target="standard"/>\n')
    doc.write('          <y:BendStyle smoothed="false"/>\n')
    doc.write('        </y:PolyLineEdge>\n')
    doc.write('      </data>\n')
    doc.write('    </edge>\n')
    

########################################
####### tests ##########################
########################################

def test1():
    pl0 = TimePlace(name = 'pp00', time = 2.)
    pl1 = TimePlace(name = 'pp11', time = 3.)
    pl2 = TimePlace(name = 'pp22', time = 4.)
    pl3 = TimePlace(name = 'pp33')
    places = [pl0, pl1, pl2, pl3]
    
    tr0 = TimeTransition(name = 'tt00', time = 5.)
    tr1 = TimeTransition(name = 'tt11', time = 3.)
    tr2 = TimeTransition(name = 'tt22', time = 2.)
    tr3 = TimeTransition(name = 'tt33', time = 1.)
    tr4 = TimeTransition(name = 'tt44', time = 2.)
    transitions = [tr0, tr1, tr2, tr3, tr4]
    
    inputs = [[1,1,0,0,0],
              [0,0,1,1,0],
              [0,0,0,0,1],
              [0,0,0,0,1]]
    
    outputs = [[1,0,0,0,0],
               [0,2,0,0,0],
               [0,0,1,0,0],
               [0,0,0,1,0]]
           
    tok = TimeToken()
    tokens = {pl0: [TimeToken.copy(tok), TimeToken.copy(tok)], pl2: [TimeToken.copy(tok)]}
    
    ptd1 = TimedPetriNet('ptd1')

    ptd1.buildPetriNet(places, transitions, inputs, outputs, tokens)
    
    return ptd1


def test2(priority = False, step = None):
    pl0 = TimePlace(name = 'pl0')
    places = [pl0]
    
    tr0 = TimeTransition(name = 'tr0', time = 1.0, minimumStartingTime = 6.0)
    tr1 = TimeTransition(name = 'tr1', time = 3.0, minimumStartingTime = 0.0)
    tr2 = TimeTransition(name = 'tr2', time = 2.0, minimumStartingTime = 2.0)
    transitions = [tr0, tr1, tr2]
    
    tok0 = TimeToken('tok0')
    tok1 = TimeToken('tok1')
    tok2 = TimeToken('tok2')
    
    if(priority):
        tok0.addPriority(pl0, [tr2])
        tok1.addPriority(pl0, [tr1])
        tok1.addPlaceClock(pl0, 50)
        tok2.addPlaceClock(pl0, 60)
    
    inputs = [[1,1,1]]
    
    outputs = [[0,0,0]]
    
    tokens = {pl0: [tok0, tok1, tok2, TimeToken.copy(tok2), TimeToken.copy(tok2)]}
    
    pt = TimedPetriNet('pt')
    
    pt.buildPetriNet(places, transitions, inputs, outputs, tokens)
    
    pt.simulation(step = step)


def test3(step = None):
    pl0 = TimePlace(name = 'pl0')
    pl1 = TimePlace(name = 'pl1')
    pl2 = TimePlace(name = 'pl2', time = 2.0)
    pl3 = TimePlace(name = 'pl3')
    pl4 = TimePlace(name = 'pl4')
    pl5 = TimePlace(name = 'pl5')
    pl6 = TimePlace(name = 'pl6')
    places = [pl0, pl1, pl2, pl3, pl4, pl5, pl6]
    
    tr0 = TimeTransition(name = 'tr0')
    tr1 = TimeTransition(name = 'tr1')
    tr2 = TimeTransition(name = 'tr2')
    tr3 = TimeTransition(name = 'tr3')
    tr4 = TimeTransition(name = 'tr4')
    tr5 = TimeTransition(name = 'tr5')
    transitions = [tr0, tr1, tr2, tr3, tr4, tr5]
    
    tok0 = TimeToken('tok0')
    tok1 = TimeToken('tok1', show = False)
    tok2 = TimeToken('tok2', show = False)
    tok = TimeToken('tok', show = False)
    
    inputs = [[1,1,1,0,0,0],
          [1,0,0,0,0,0],
          [0,0,0,1,1,0],
          [0,1,0,0,0,0],
          [0,0,0,0,1,1],
          [0,0,1,0,0,0],
          [0,0,0,0,0,1]]
    
    outputs = [[0,0,0,0,0,0],
           [0,0,0,1,0,0],
           [1,0,0,0,0,0],
           [0,0,0,0,1,0],
           [0,1,0,0,0,0],
           [0,0,0,0,1,1],
           [0,0,1,0,0,0]]
    
    tokens = {pl0 : [tok0, tok1, tok2], pl1 : [tok, TimeToken.copy(tok)], pl3 : [TimeToken.copy(tok)]}
    
    tok0.addPriority(pl0, [tr0])
    tok0.addPriority(pl2, [tr4])
    tok0.addPlaceClock(pl2, 3)
    tok1.addPriority(pl0, [tr1])
    tok1.addPriority(pl2, [tr4,tr3])
    tok1.addPlaceClock(pl0, 1)
    tok2.addPriority(pl0, [tr2, tr0])
    tok2.addPlaceClock(pl0, 2)
    
    pt = TimedPetriNet('pt')
    
    pt.buildPetriNet(places, transitions, inputs, outputs, tokens)
    
    pt.simulation(step = step)
    

def test_RCPSP(step = None):
    rooms = []
    for i in range(31):
        rooms.append(TimePlace(i, 0))
    rooms[0].time = 2
    rooms[2].time = 2
    rooms[6].time = 2
    rooms[7].time = 10
    rooms[14].time = 10
    rooms[18].time = 2
    rooms[19].time = 130
    rooms[22].time = 5
    rooms[23].time = 2
    rooms[26].time = 20
    rooms[27].time = 2
    rooms[28].time = 2
    rooms[30].time = 2
    
    ac1 = TimeTransition('Entrance SU', 0)
    ac2 = TimeTransition('Entrance Induction room', 0)
    ac3 = TimeTransition('Start AN', 0)
    ac4 = TimeTransition('Entrance OR', 0)
    ac5 = TimeTransition('Start preparation AN', 0)
    ac6 = TimeTransition('End Induction', 0)
    ac7 = TimeTransition('Patient ready for surgery', 0)
    ac8 = TimeTransition('Start Preparation OP', 0)
    ac9 = TimeTransition('OR free', 0)
    ac10 = TimeTransition('End preparation OP', 0)
    ac11 = TimeTransition('Start surgical procedure', 0)
    ac12 = TimeTransition('Incicsion', 0)
    ac13 = TimeTransition('Closure', 0)
    ac14 = TimeTransition('End surgical procedure', 0)
    ac15 = TimeTransition('End post-OP', 0)
    ac16 = TimeTransition('End AN', 0)
    ac17 = TimeTransition('End post-AN', 0)
    ac18 = TimeTransition('Exit OR', 0)
    ac19 = TimeTransition('Patient in PACU/ICU', 0)
    ac20 = TimeTransition('End presence AD', 0)
    ac21 = TimeTransition('Exit SU', 0)
    actions = [ac1, ac2, ac3, ac4, ac5, ac6, ac7, ac8, ac9, ac10, ac11, ac12, ac13, ac14,
               ac15, ac16, ac17, ac18, ac19, ac20, ac21]

    inputs = []
    inputs.append([1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0])
    inputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1])
    
    outputs = []
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0])
    outputs.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0])
    
    tok = TimeToken()
    tokens = {rooms[0]: [TimeToken.copy(tok)], rooms[3]: [TimeToken.copy(tok)], rooms[5]: [TimeToken.copy(tok)], rooms[10]: [TimeToken.copy(tok)], rooms[12]: [TimeToken.copy(tok)], rooms[13]: [TimeToken.copy(tok)], rooms[20]: [TimeToken.copy(tok)]}
    
    pn = TimedPetriNet('pn')
    
    pn.buildPetriNet(rooms, actions, inputs, outputs, tokens)

    pn.simulation(step = step)

    
def test_create_petrinet():
    src = open('petriNet_without_AN.graphml','r')
    pt = read_graph(src)
    return pt