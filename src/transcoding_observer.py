#!/usr/bin/env python3
# -*- coding: utf8 -*-

import abc

class TranscodingObserver(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def update(self):
        ...
