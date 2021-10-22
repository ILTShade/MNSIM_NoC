#-*-coding:utf-8-*-
"""
@FileName:
    base_router.py
@Description:
    Base router class
@CreateTime:
    2021/10/08 18:46
"""
from abc import abstractmethod
from mnsim_noc.base import Component


class BaseRouter(Component):
    REGISTRY = "router"

    def __init__(self):
        super().__init__(self)

    @abstractmethod
    def assign(self, transfer_data, wire_state):
        pass
