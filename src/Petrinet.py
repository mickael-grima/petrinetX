# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

from Token import Token
from Place import Place
from Transition import Transition
from utils.tools import pref_func
import logging


class PetriNet:
    """This class represents a petriNet
    """

    def __init__(self, name='no name', logger=logging):
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
        """ Dictionnary of ``place`` to whose we associate a dictionnary of transitions: number of tokens.
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
        self.logger = logger

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

    def removeToken(self, place, *tokens):
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

                * ``new_dct_tkn = False`` : see the method
                            :func:`insertTokenQueue <petrinet_simulator.Transition.insertTokenQueue>`

                * ``place_presence = False`` : see the attribute
                            :attr:`tokenQueueAfterFire <petrinet_simulator.Transition.tokenQueueAfterFire>`

                * ``nb_tok = -1`` : see the attribute
                            :attr:`tokenQueueAfterFire <petrinet_simulator.Transition.tokenQueueAfterFire>`

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
        if self.downplaces.get(transition) is not None and self.downplaces[transition].get(place) is not None:
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

              * ``tokens = {}``: Tokens to add in the petrinet. For each place has to be associated a list, dict or
                                 tuple of :class:`TimeToken <petrinet_simulator.TimeToken>`

            .. Note:: ``inputs`` and ``outputs`` can have several types:

                * *List* or *tuple*: In this case they are represented by a matrix whose range represents
                                     ``transitions`` and lines ``places``. The range j and the line i give the output or
                                     input between the transition whose associated number in
                                     :attr:`self.transitions <petrinet_simulator.PetriNet.transitions>` is j and
                                     ``place`` whose associated number in
                                     :attr:`self.places <petrinet_simulator.PetriNet.places>` is i.
                * *Dict*: In this case they must have the same form as
                          :attr:`self.transitions <petrinet_simulator.PetriNet.transitions>` and
                          :attr:`self.places <petrinet_simulator.PetriNet.places>`.

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

    # -------------------------------------------------------
    # --------------- other functions -----------------------
    # -------------------------------------------------------

    # TODO to adapte, to document
    def reachabilityGraph(self, initialToken):
        graph = {}
        visited = {}
        queue = [initialToken]
        while len(queue) > 0:
            token = queue[0]
            visited.setdefault(tuple(token), token)
            queue.remove(token)
            ets = self.enabledTransitionsSet(token)
            neighbours = {}
            for t, c in ets.iteritems():
                tk = self.fire(t, token)
                neighbours.setdefault(t, tk)
                b = True
                for c, v in visited.iteritems():
                    b2 = False
                    for i in range(len(tk)):
                        if(tk[i] != v[i]):
                            b2 = True
                    b = b and b2
                if b is True:
                    queue.append(tk)
            graph.setdefault(tuple(token), neighbours)
        return graph

    def changeFireToken(self, place, token, ets):
        """ Change the attribute :attr:`fire <petrinet_simulator.TimeToken.fire>` of ``token`` and adapte the enable
            transitions Set ``ets`` given by the method
            :func:`enabledTransitionsSet <petrinet_simulator.PetriNet.enabledTransitionsSet>`

            :param place: Place where ``token`` is located
            :type place: :class:`Place <petrinet_simulator.Place>`
            :param token: Token to modify
            :type token: :class:`TimeToken <petrinet_simulator.TimeToken>`
            :param ets: Enabled transition set build by the method
                        :func:`enabledTransitionsSet <petrinet_simulator.PetriNet.enabledTransitionsSet>`
            :type ets: dict

            .. Warning:: ``token`` has to be on ``place``, otherwise an error is raised
        """
        assert token in place.token
        token.fire = not token.fire

        for t, n in (self.inputs.get(place) or {}).iteritems():
            if t in ets and not self.isEnabled(t):
                del ets[t]
            if self.isEnabled(t):
                ets.setdefault(t, self.transitions[t])

    def getEnabledToken(self, place, transition):
        """ Get every enable token on upplaces regarding the given ``transition``

            :param place: *
            :type place: :class:`Place <Place.Place>`
            :param transition: *
            :type transition: :class:`Transition <Transition.Transition>`

            :returns: generator ok tokens
        """
        # are there enough token on each place up
        for tok in place.token:
            is_firing = place not in tok.priority or transition == tok.priority[place]['priority'][0]
            if not is_firing:
                is_firing = tok.priority[place]['pref'] == 'time' and transition in tok.priority[place]['priority']
            if tok.fire and is_firing:
                yield tok

    def isEnabled(self, transition):
        """ Compute if ``transition`` can fire. A transition can fire if:

              * It exists in the PetriNet
              * On each place up, there are enough token with the following properties:
                * ``transition`` belong to the priority list of the token
                * The token can fire
              * Every name in the first list of
                :attr:`transition.tokenQueue <petrinet_simulator.Transition.tokenQueue>` belongs at least to one of
                the enable token above.

            :param transition: *
            :type transition: :class:`Transition <petrinet_simulator.Transition>`

            :returns: True if ``transition`` is enable, else False
        """
        # Does it exist in the petrinet
        if self.transitions.get(transition) is None:
            self.logger.warning("Transition %s doesn't exist in petriNet %s!" % (str(transition), self.name))
            return False

        tokens = []
        for place, nb in self.upplaces[transition].iteritems():
            niter = 0
            for tok in self.getEnabledToken(place, transition):
                tokens.append(tok)
                niter += 1
            if niter < nb:
                return False
        names = sum(map(lambda tok: tok.name.split('_'), tokens), [])  # names of enables tokens

        # Every name to the first list of transition.tokenQueue has to belong at least to one of the token on an upplace
        res = set(transition.tokenQueue[0]).issubset(names) if transition.tokenQueue else True

        # On each upplace, do we have enough token
        for p, nb in self.upplaces[transition].iteritems():
            res = res and len(tokens or []) >= nb

        return res

    def getPrioritySortedToken(self, place, transition):
        priority_tokens = []
        for token in self.getEnabledToken(place, transition):
            priority_value, i = token.get_priority_value(place, transition), 0
            # Insert the token in the list. Make sure that the list is sorted
            while i < len(priority_tokens):
                if priority_tokens[i][1] <= priority_value:
                    break
                i += 1
            priority_tokens.append((token, priority_value))
        for token, _ in priority_tokens:
            yield token

    # return a sequence of token with the right priority and the right number of token,
    # sorted considering the tokens clocks
    def getSortedNextFiredToken(self, place, transition):
        """ Compute a generator of token's that belong to ``place`` enable for ``transition``
            This generator is sorted regarding the clock's and the minimumStartingTime of each token
            The first criteria to order the tokens is **the appartenance to
            transition.**:attr:`tokenQueue <petrinet_simulator.Transition.tokenQueue>`, the second is **the time**

            :param place: *
            :type place: :class:`Place <petrinet_simulator.Place>`
            :param transition: *
            :type transition: :class:`Transition <petrinet_simulator.Transition>`

            .. Warning:: If there is NO input between ``place`` and ``transition``, the method return an empty generator
        """
        # introduce two list:
        #   - list concerning the token that have to contain the name wanted by transition
        #   - list with the strongest priority
        name_first_tokens = {}
        priority_tokens = [tok for tok in self.getPrioritySortedToken(place, transition)]

        # counter to know if enough token up are available (concerning the name)
        tokens_words = {}
        nb_priority = self.inputs[place][transition]

        if transition.tokenQueue:
            # We first sort the token by priority and save it with respect to their names
            for token in self.getEnabledToken(place, transition):
                tokens_words.setdefault(token, [])
                for word in token.name.split('_'):
                    if word in transition.tokenQueue:
                        name_first_tokens.setdefault(word, set())
                        name_first_tokens[word].add(token)
                        tokens_words[token].append(word)

            # Then we keep the most priority tokens iff it always exist at least a token for each required name
            N = len(name_first_tokens)
            n, nb_priority = 0, nb_priority - N
            while n < nb_priority:
                token = priority_tokens[n]
                if set.intersection(*name_first_tokens.itervalues()).difference([token]) >= N:
                    for word in tokens_words[token]:
                        name_first_tokens[word].remove(token)
                        n += 1
                else:
                    del priority_tokens[n]

            for word, dct in name_first_tokens.iteritems():
                yield dct.iterkeys().next()

        for token in priority_tokens[:nb_priority]:
            yield token

    def enabledTransitionsSet(self):
        """ Build the set of enabled transitions

            :returns: A dictionnary :class:`Transition <petrinet_simulator.Transition>`: int
        """
        return {t: c for t, c in self.transitions.iteritems() if self.isEnabled(t)}

    def adapteEnabledTransitionsSet(self, transitions, ets):
        n = 0
        for t in transitions:
            is_enabled = self.isEnabled(t)
            if t in ets and not is_enabled:
                del ets[t]
                n += 1
            if t not in ets and is_enabled:
                ets.setdefault(t, self.transitions[t])
                n += 1
        return n

    def isBlocked(self):
        """ Compute if the there still are enabled transitions or Note

            :returns: A boolean
        """
        for t, c in self.transitions.iteritems():
            if self.isEnabled(t):
                return False
        return True

    def isInStructuralConflict(self, transition1, transition2):
        """ Check if ``transition1`` and ``transition2`` are in structural conflict,
            i.e. one token or more can be fired by both transitions

            :param transition1: *
            :type transition1: :class:`Transition <petrinet_simulator.Transition>`
            :param transition2: *
            :type transition2: :class:`Transition <petrinet_simulator.Transition>`

            :returns: A boolean
        """
        if self.upplaces.get(transition1) is not None:
            for p, nb in self.upplaces[transition1].iteritems():
                if self.upplaces.get(transition2) is not None and p in self.upplaces[transition2]:
                    return True
        return False

    def isAllInStructuralConflict(self, transitions):
        """ Check if each transition in ``transitions`` is not in structural conflict with an other one.

            :param transitions: *
            :type transitions: List, dict or tuple
        """
        for tr1 in transitions:
            for tr2 in transitions:
                if tr1 != tr2 and self.isInStructuralConflict(tr1, tr2):
                    return True
        return False

    def isInBehavioralConflict(self, transition1, transition2):
        """ Check if ``transition1`` and ``transition2`` are in behavioral conflict,
            i.e. both transitions are enable but there are not enough tokens on places up
            in order to activate both transitions

            :param transition1: *
            :type transition1: :class:`Transition <petrinet_simulator.Transition>`
            :param transition2: *
            :type transition2: :class:`Transition <petrinet_simulator.Transition>`

            :returns: A boolean
        """
        b = True
        for p, nb in self.token.iteritems():
            b = b and nb >= (self.inputs[p][transition1] + self.inputs[p][transition2])
        return (not b and self.isEnabled(transition1) and self.isEnabled(transition2))

    def isAllInBehavioralConflict(self, transitions):
        """ Check if each transition in ``transitions`` is not in behavioral conflict with an other one.

            :param transitions: *
            :type transitions: List, dict or tuple
        """
        for tr1 in transitions:
            for tr2 in transitions:
                if tr1 != tr2 and self.isInBehavioralConflict(tr1, tr2):
                    return True
        return False

    def conflictPlaces(self, transition1, transition2):
        """ Compute the places that are shared by both ``transition1`` and ``transition2``

            :param transition1: *
            :type transition1: :class:`Transition <petrinet_simulator.Transition>`
            :param transition2: *
            :type transition2: :class:`Transition <petrinet_simulator.Transition>`

            :returns: Dictionnary :class:`Place <petrinet_simulator.Place>`: int
        """
        places = {}

        if self.upplaces.get(transition1) is not None:
            for p1, nb1 in self.upplaces[transition1].iteritems():
                if self.upplaces.get(transition2) is not None and p1 in self.upplaces[transition2]:
                    places.setdefault(p1, nb1)

        return places

    def AllConflictPlaces(self, transitions):
        """ Compute all the conflict places between each couple of transitions in ``transitions``

            :param transitions: *
            :type transitions: List, dict or tuple

            :returns: Dictionnary :class:`Place <petrinet_simulator.Place>`: int
        """
        places = {}
        if isinstance(transitions, list) or isinstance(transitions, dict) or isinstance(transitions, tuple):
            for t1 in transitions:
                for t2 in transitions:
                    places.update(self.conflictPlaces(t1, t2))
        return places

    def pref(self, transition):
        """ The preference of ``transition`` is computed following these steps:
                * We consider the tokens up to ``transition`` and enabled for ``transition`` using the method
                  :func:`getSortedNextFiredToken <petrinet_simulator.PetriNet.getSortedNextFiredToken>`
                * For each token above we compute the position ``ind`` of ``transition`` in
                  :attr:`token.priority <petrinet_simulator.Token.priority>`
                * We apply the method :func:`pref_func <petrinet_simulator.Tools.pref_func>`
                  that compute a value for ``ind``
                * We sum all the given value and we return the average

            :param transition: *
            :type transition: :class:`Transition <petrinet_simulator.Transition>`

            :returns: A float
        """
        result = []
        for p, n in (self.upplaces.get(transition) or {}).iteritems():
            for tok in self.getSortedNextFiredToken(p, transition):
                if tok.priority.get(p) is not None:
                    result.extend(map(
                        lambda tr: pref_func(tok.priority[p]['priority'].index(tr)),
                        filter(lambda tr: tr == transition, tok.priority[p]['priority'])
                    ))

        return sum(result) / len(result) if result else 0.0

    def mostPriorityTransition(self, *transitions):
        """ For each transition in ``transitions``, we keep the one that has the biggest preference compute using
            the method :func:`pref <petrinet_simulator.PetriNet.pref>`

            :param transitions: *
            :type transitions: List, dict or tuple

            :returns: An object of class :class:`Transition <petrinet_simulator.Transition>`
                      or None if no transition are found
        """
        try:
            return sorted(transitions, key=self.pref)[-1]
        except Exception as e:
            self.logger.warning(str(e))
            return None

    # -------------------------------------------------------
    # -------------- representation functions ---------------
    # -------------------------------------------------------

    def __fireToken(self, transition, ets):
        tok_save, transitions_save = [], {}

        # save the previous token and remove the token that were fired
        if self.upplaces.get(transition) is not None:
            for p in self.upplaces[transition].iterkeys():
                for tok in self.getSortedNextFiredToken(p, transition):
                    tok_save.append(tok)
                    self.removeToken(p, tok)
                transitions_save.update(self.inputs.get(p) or {})

        # If a transition is not enabled anymore then its clock is reinitialized
        for t in transitions_save.iterkeys():
            if ets.get(t) and not self.isEnabled(t):
                del ets[t]

        return tok_save

    def __updateTokenQueue(self, transition, fired_tokens):
        # we remove the token of transition.tokenQueue
        if transition.tokenQueue:
            del transition.tokenQueue[0]

        # We adapte the tokenQueue of targeted transitions
        if transition.tokenQueueAfterFire:
            for tkk, dct in transition.tokenQueueAfterFire[0].iteritems():
                tkk_save = [t for t in tkk]

                # if all tokens in tkk are in the firing token, then we apply the token queue after fire
                for tok in fired_tokens:
                    i = 0
                    while i < len(tkk_save):
                        tkn = tkk_save[i]
                        if tkn in tok.name.split('_'):
                            del tkk_save[i]
                            continue
                        i += 1
                    if not tkk_save:
                        break

                for tr, attr in dct.iteritems():
                    for tab in attr['tokenQueue']:
                        self.insertTokenQueue(tr, [el for el in tab], place_presence=attr['place_presence'],
                                              nb_tok=attr['nb_tok'])
            del transition.tokenQueueAfterFire[0]

    def __updateAdvancedProperties(self, tok, transition, tok_save, ets):
        # priority after fire
        for t in tok_save:
            for tr, dic in t.priorityAfterFire.iteritems():
                if tr == transition:
                    for loc, prt in dic.iteritems():
                        if loc == 'self':
                            for pl, attr in prt.iteritems():
                                tok.addPriority(pl, attr['priority'], pref=attr['pref'])
                        else:
                            for token in loc[0].token:
                                if loc[1] in token.name.split('_'):
                                    for pl, trs in prt.iteritems():
                                        token.addPriority(pl, trs)
                else:
                    for loc, prt in dic.iteritems():
                        for pl, attr in prt.iteritems():
                            tok.addPriorityAfterFire(tr, {pl: attr['priority']}, location=loc, pref=attr['pref'])
            if t.fireHeritance.get(transition) is not None:
                for pl, ts in t.fireHeritance[transition].iteritems():
                    for tt in pl.token:
                        if tt.name in ts:
                            if not tt.fire:
                                self.changeFireToken(pl, tt, ets)

    def __getTokenAfterFire(self, transition, ets, tok_save):
        tok = Token()

        # add a name and first priorities to tok
        tok.addFirstProperties(*tok_save)

        # update advanced properties
        self.__updateAdvancedProperties(tok, transition, tok_save, ets)

        return tok

    def __updateAfterFiring(self, transition, token, ets):
        transitions_save = {}
        # Add token to places after the transition that fired
        for p, n in (self.downplaces.get(transition) or {}).iteritems():
            for i in range(n):
                self.addToken(p, token.copy())
            if self.inputs.get(p):
                transitions_save.update(self.inputs.get(p) or {})

        # If a transition is enabled we add it to ets
        ets.update({t: c for t, c in transitions_save.iteritems() if ets.get(t) and self.isEnabled(t)})

    def __adaptePetriNet(self, transition, ets):
        fired_tokens = self.__fireToken(transition, ets)

        # We adapte the tokenQueue of targeted transitions and of transition
        self.__updateTokenQueue(transition, fired_tokens)

        # create the token after the fire
        token = self.__getTokenAfterFire(transition, ets, fired_tokens)

        # Update the places and ets after the firing
        self.__updateAfterFiring(transition, token, ets)

    def computeFiringTransition(self, ets):
        """ Among the given transitions in ``ets``, this method compute the next transition to fire regarding priority,
            preference and time (only for :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`)

            :param ets: set of enabled transitions
            :type ets: dict

            :returns: an object of class :class:`Transition <petrinet_simulator.Transition>`

            .. Note:: To create ets we can invoque the method
                      :func:`enabledTransitionsSet <petrinet_simulator.PetriNet.enabledTransitionsSet>`
        """
        return self.mostPriorityTransition(*ets.iterkeys())

    def fire(self, transition, ets):
        """ Execute the firing of ``transition``, adapte ``ets`` and all places and tokens in the PetriNet

            :param transition: transition that fired
            :type transition: :class:`Transition <petrinet_simulator.Transition>`
            :param ets: set of enabled transitions
            :type ets: dict

            .. Warning:: ``ets`` must contain only enable transitions, otherwise an Error can be raised
        """
        # adapte the places
        self.__adaptePetriNet(transition, ets)

    def oneFireSimulation(self, ets):
        """ Compute the next firing transition and execute the firing: the two methods called are
            :func:`computeFiringTransition <petrinet_simulator.PetriNet.computeFiringTransition>` and
            :func:`fire <petrinet_simulator.PetriNet.fire>`

            :param ets: set of enabled transitions
            :type ets: dict

            :returns: an object of class :class:`Transition <petrinet_simulator.Transition>`
        """
        # compute the minimum of time for enabled transitions, and choose the transition
        transition = self.mostPriorityTransition(*ets.iterkeys())

        # fire and adapte each clocks
        self.fire(transition, ets)

        # we return the new token
        return transition

    def simulation(self, show=True, niter=float('nan')):
        if not isinstance(show, bool):
            raise TypeError('Boolean expected, got a %s instead' % show.__class__.__name__)

        if show:
            print 'beginning of the simulation'
            print ''

        if self.initialState == {}:
            self.setInitialState()
            ets = self.enabledTransitionsSet()

        n = 0
        while len(ets) != 0 and not n >= niter:
            transition = self.oneFireSimulation(ets)
            n += 1

            if transition.show and show:
                print transition.name + ' fired'
                print ''

        if show:
            print 'end of the simulation'
