# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

import unittest
from src.utils.builder import build_chain_petrinet, build_simple_conflicts
from src.Tools import concatenate


class ToolsTest(unittest.TestCase):
    """ test the tools
    """
    def testConcatenate(self):
        """ considering two petrinets, test wether the concatenate function returned the right result
        """
        pn1 = build_chain_petrinet(size=2)
        pn2 = build_simple_conflicts()

        pn = concatenate(pn1, pn2)
