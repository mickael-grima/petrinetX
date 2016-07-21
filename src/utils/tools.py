# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 21:38:37 2016

@author: Mickael Grima
"""


# the lowest is ind or clock, the highest is the function
def pref_funct(ind):
    """ Higher ``ind`` is, lower the result is

        :param ind: *
        :type ind: int, long or float

        :returns: float
    """
    return 10.0 / (1 + ind)
