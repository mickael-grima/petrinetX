# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 21:38:37 2016

@author: Mickael Grima
"""


def get_id(obj):
    return hash(obj)


def pref_func(x):
    """ Higher ``x`` is, lower the result is

        :param x: *
        :type x: int, long or float

        :returns: float
    """
    return 10.0 / (1.0 + x)
