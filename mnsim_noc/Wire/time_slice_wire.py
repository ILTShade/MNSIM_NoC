# -*-coding:utf-8-*-
"""
@FileName:
    time_slice_tile.py
@Description:
    Wire Class for time slice
@CreateTime:
    ---
"""
from mnsim_noc.Wire import BaseWire


class TimeSliceWire(BaseWire):
    NAME = "time_slice_tile"

    def __init__(self, position):
        self.position = position
        self.wire_id = BaseWire.get_tile_id(position)
        self.state = None

    def set_wire_task(self, wire_tasks):
        pass

    def update_time_slice(self):
        pass
