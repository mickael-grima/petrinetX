# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 21:38:37 2016

@author: Mickael Grima
"""

from PetriNet import PetriNet
from TimePetrinet import TimePetriNet


def concatenate(petriNet1, petriNet2, name='no name', input_connections=None, output_connections=None):
    """ Build a global petriNet from the two given petrinets.

        :param petriNet1: *
        :type petriNet1: :class:`PetriNet <petrinet_simulator.PetriNet>`
        :param petriNet2: *
        :type petriNet2: :class:`PetriNet <petrinet_simulator.PetriNet>`

        * options:

            * ``name = 'no name'``: the name of the return petriNet
            * ``input_connections = None``: the input's connections added to the return petriNet.
                                            It's a tuple of place, transition
            * ``output_connections = None``: the output's connections added to the return petriNet.
                                             It's a tuple of place, transition

        :returns: an object of class :class:`PetriNet <petrinet_simulator.PetriNet>`
    """
    if not isinstance(petriNet1, PetriNet):
        raise TypeError('PetriNet expected, got a %s instead' % petriNet1.__class__.__name__)
    if not isinstance(petriNet2, PetriNet):
        raise TypeError('PetriNet expected, got a %s instead' % petriNet2.__class__.__name__)

    minimumDate = None
    if petriNet1.startDate is not None:
        if petriNet2.startDate is not None:
            dur = (petriNet1.startDate - petriNet2.startDate).total_seconds() / 60.
            if(dur > 0):
                minimumDate = petriNet2.startDate
            else:
                minimumDate = petriNet1.startDate
        else:
            minimumDate = petriNet1.startDate
    else:
        if petriNet2.startDate is not None:
            minimumDate = petriNet2.startDate

    if isinstance(petriNet1, TimePetriNet) or isinstance(petriNet2, TimePetriNet):
        result = TimePetriNet(str(name), startDate=minimumDate)
    else:
        result = PetriNet(str(name))

    # add the places and tokens
    for p1 in petriNet1.places.iterkeys():
        result.addPlace(p1)
    for p2 in petriNet2.places.iterkeys():
        result.addPlace(p2)

    # add tokens
    result.token.update(petriNet1.token)
    result.token.update(petriNet2.token)

    # add the transitions
    for t1 in petriNet1.transitions.iterkeys():
        result.addTransition(t1)
    for t2 in petriNet2.transitions.iterkeys():
        result.addTransition(t2)

    # create the inputs
    result.inputs.update(petriNet1.inputs)
    result.inputs.update(petriNet2.inputs)
    result.outputs.update(petriNet1.outputs)
    result.outputs.update(petriNet2.outputs)
    result.upplaces.update(petriNet1.upplaces)
    result.upplaces.update(petriNet2.upplaces)
    result.downplaces.update(petriNet1.downplaces)
    result.downplaces.update(petriNet2.downplaces)

    # add the input_connections and output_connections
    if input_connections is not None:
        for t in input_connections:
            result.addInput(t[0], t[1])
    if output_connections is not None:
        for t in output_connections:
            result.addOutput(t[0], t[1])

    return result


def read_graph(src):
    """ For a given ``src``, make a petriNet. ``src`` has to come from a document whose extension is graphml.
        The places in ``src`` have to be nodes with ellipse form, and the transitions nodes with rectangle form.

        :param src:
        :type src: docfile

        :returns: An object of class :class:`TimedPetriNet <petrinet_simulator.TimedPetriNet>`
    """
    lines = src.readlines()

    while True:
        line = lines[0]
        data = line.split()
        if(data[2] == "<graph"):
            break
        else:
            del lines[0]

    pt = TimedPetriNet()
    nodes, edges = [], []

    i = 0
    while i < len(lines):
        line = lines[i][:-2] if lines[i].endswith('\n') else lines[i]
        data = line.split()

        if "<node" in data and 'yfiles.foldertype="group">' not in data:
            end_node = ""
            j = 0
            word = data[j]
            while(word == ''):
                end_node += ' '
                j += 1
                word = data[j]
            end_node += "</node>\n"

        # --- if the node a simple node is ---
        lines_node = []
        while lines[i] != end_node:
            lines_node.append(lines[i].rstrip('\n'))
            i += 1
        lines_node.append(lines[i].rstrip('\n'))

        nodes.append(lines_node)

        if "<edge" in data:
            end_edge = ''
            j = 0
            word = data[j]
            while(word == ''):
                end_edge += ' '
                j += 1
                word = data[j]
            end_edge += "</edge>\n"

        # --- if the edge a simple edge is ---
        lines_edge = []
        while lines[i] != end_edge:
            lines_edge.append(lines[i].rstrip('\n'))
            i += 1
        lines_edge.append(lines[i].rstrip('\n'))

        edges.append(lines_edge)

        i += 1

    for lines in nodes:
        node, typ, pos = __create_node(lines)
        if typ == "transition":
            pt.addTransition(node, pos=pos)
        if typ == "place":
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
