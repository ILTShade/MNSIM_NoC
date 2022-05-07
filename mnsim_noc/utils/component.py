#-*-coding:utf-8-*-
"""
@FileName:
    base.py
@Description:
    component for all other parts
@CreateTime:
    2021/10/08 17:50
"""
from mnsim_noc.utils import getLogger, RegistryMeta

class Component(object, metaclass=RegistryMeta):
    """
    component for all other parts
    init logger and other things
    """
    __metaclass__ = RegistryMeta
    def __init__(self):
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = getLogger(self.__class__.__name__)
        return self._logger

    def __getstate__(self):
        state = self.__dict__.copy()
        if "_logger" in state:
            del state["_logger"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._logger = None
