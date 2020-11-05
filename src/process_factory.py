#!/usr/bin/env python3
# -*- coding: utf8 -*-

import abc

#class ProcessMetaFactory(object, metaclass=abc.ABCMeta):
class ProcessFactory(object, metaclass=abc.ABCMeta):
    """
    Factory, producing a list of of factories???
    """

    @abc.abstractmethod
    def __init__(self):
        # list of factory methods for process creation
        self.processFactories = list()
    
    @abc.abstractmethod
    def factoryMethods(self):
        ...
