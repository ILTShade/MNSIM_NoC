#-*-coding:utf-8-*-
"""
@FileName:
    base_time_slice_wire.py
@Description:
    Base Wire Class for time slice
@CreateTime:
    2021/10/08 18:17
"""
from abc import abstractmethod
from mnsim_noc import Component

class BaseTimeSliceWire(Component):
    REGISTRY = "time_slice_wire"

    def __init__(self, position):
        self.position = position
        self.wire_id = BaseTimeSliceWire.get_tile_id(position)
        self.state = None

    @classmethod
    def get_tile_id(cls, position):
        return "{}_{}_{}".format(position[0], position[1], position[2])

    @abstractmethod
    def set_wire_task(self, wire_tasks):
        pass

    @abstractmethod
    def update_time_slice(self):
        pass
