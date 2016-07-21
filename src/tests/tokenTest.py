# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import sys
sys.path.append("/home/mickael/Documents/projects/petrinetX/src/")

import unittest
from Token import Token


class TokenTest(unittest.TestCase):
    """ test everything about Token class
    """
    def setUp(self):
        self.token = Token(name='name_castle_city', show=True, fire=True)

    def testCopy(self):
        """ does token.copy() copy everything?
        """
        tok = self.token.copy()
        for key in tok.__dict__.iterkeys():
            self.assertNotEqual(tok.__dict__[key] or '', self.token.__dict__[key] or {})


if __name__ == '__main__':
    unittest.main()
