# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""


class Simulator(object):
    def __init__(self):
        pass

    def next(self):
        pass

    def previous(self):
        pass

    def has_next(self):
        return False

    def to_image(self):
        raise NotImplementedError()

    def reinitialize(self):
        pass
