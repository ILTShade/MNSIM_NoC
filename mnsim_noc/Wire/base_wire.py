# -*-coding:utf-8-*-
"""
@FileName:
    base_wire.py
@Description:
    Base Wire Class for time slice
@CreateTime:
    2021/10/08 18:17
"""
from abc import abstractmethod
from mnsim_noc import Component


class BaseWire(Component):
    REGISTRY = "wire"

    def __init__(self, position):
        self.position = position
        self.wire_id = BaseWire.get_wire_id(position)

    @classmethod
    def get_wire_id(cls, position):
        # North:0; West:1; South:2; East:3;
        return "{}_{}_{}".format(position[0], position[1], position[2])

    @abstractmethod
    def set_wire_task(self, wire_tasks):
        pass

    @abstractmethod
    def update_time_slice(self):
        pass
