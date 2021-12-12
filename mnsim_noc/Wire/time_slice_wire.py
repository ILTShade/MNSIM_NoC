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
        super().__init__(position)
        # data transmitted on the wire
        # format: (x, y, end_tile_id, layer)
        self.data = None
        # Number of time slice required for finishing the transmission
        self.state = 0
        # data transferred during simulation
        self.transferred_data = 0

    def set_wire_task(self, wire_tasks):
        # Format:(x, y, end_tile_id, length, layer, is_first, is_last)
        self.state = wire_tasks[3]
        # data Format:(x, y, end_tile_id, layer, is_first, is_last)
        self.data = wire_tasks[0:3] + wire_tasks[4:7]
        self.transferred_data += wire_tasks[3]

    def update_time_slice(self, n):
        if self.state > 0:
            self.state -= n
        if self.state == 0 and self.data:
            # return data to update tile
            tmp_data = self.data
            self.data = None
            return tmp_data

    def get_roofline(self):
        return round(self.transferred_data)
