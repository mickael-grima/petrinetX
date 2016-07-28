# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

from Place import Place
from Transition import Transition
from Token import Token
from Petrinet import PetriNet
from TimePlace import TimePlace
from TimeTransition import TimeTransition
from TimeToken import TimeToken
from TimePetrinet import TimePetriNet


def build_chain_petrinet(size=10):
    """ build a petrinet as a chain, with given size
    """
    places = [Place(name='p%s' % i) for i in range(size)]
    transitions = [Transition(name='t%s' % i) for i in range(size)]

    inputs = {places[i]: {transitions[i]: 1} for i in range(size)}
    outputs = {places[i + 1]: {transitions[i]: 1} for i in range(size - 1)}

    pn = PetriNet(name='pn')
    pn.buildPetriNet(places, transitions, inputs, outputs)

    return pn


def build_simple_conflicts():
    """ build a petrinet where a place has two possible transitions
    """
    places = [Place(name='p%s' % i) for i in range(3)]
    transitions = [Transition(name='t%s' % i) for i in range(2)]

    inputs = {places[0]: {transitions[0]: 1, transitions[1]: 1}}
    outputs = {places[1]: {transitions[0]: 1}, places[2]: {transitions[1]: 1}}

    pn = PetriNet()
    pn.buildPetriNet(places, transitions, inputs, outputs)

    return pn


def build_small_petrinet():
    pl0 = Place(name='p0')
    pl1 = Place(name='p1')
    pl2 = Place(name='p2')
    pl3 = Place(name='p3')
    places = [pl0, pl1, pl2, pl3]

    tr0 = Transition(name='t0')
    tr1 = Transition(name='t1')
    tr2 = Transition(name='t2')
    tr3 = Transition(name='t3')
    tr4 = Transition(name='t4')
    transitions = [tr0, tr1, tr2, tr3, tr4]

    inputs = [[1, 1, 0, 0, 0],
              [0, 0, 1, 1, 0],
              [0, 0, 0, 0, 1],
              [0, 0, 0, 0, 1]]

    outputs = [[1, 0, 0, 0, 0],
               [0, 2, 0, 0, 0],
               [0, 0, 1, 0, 0],
               [0, 0, 0, 1, 0]]

    pn = PetriNet('pn1')
    pn.buildPetriNet(places, transitions, inputs, outputs)

    return pn


def build_parallel_chain_petrinet(size=10, branchs=2):
    """ Build ``branchs`` chain petrinet of size ``size``
    """
    places = [Place(name='p_%s_%s' % (b, s)) for b in range(branchs) for s in range(size)]
    transitions = [Transition(name='t_%s_%s' % (b, s)) for b in range(branchs) for s in range(size)]

    inputs, outputs = {}, {}
    for b in range(branchs):
        inputs.update({places[size * b + s]: {transitions[size * b + s]: 1} for s in range(size)})
        outputs.update({places[size * b + s + 1]: {transitions[size * b + s]: 1} for s in range(size - 1)})

    pn = PetriNet(name='pn')
    pn.buildPetriNet(places, transitions, inputs, outputs)

    return pn


def build_RCPSP_petrinet():
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
    tokens = {
        rooms[0]: [TimeToken.copy(tok)],
        rooms[3]: [TimeToken.copy(tok)],
        rooms[5]: [TimeToken.copy(tok)],
        rooms[10]: [TimeToken.copy(tok)],
        rooms[12]: [TimeToken.copy(tok)],
        rooms[13]: [TimeToken.copy(tok)],
        rooms[20]: [TimeToken.copy(tok)]
    }

    pn = TimePetriNet('pn')

    pn.buildPetriNet(rooms, actions, inputs, outputs, tokens)

    return pn
