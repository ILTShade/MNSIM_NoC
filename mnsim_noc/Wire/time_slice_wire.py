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
        super().__init__(self, position)
        # data transmitted on the wire
        # format: (x, y, end_tile_id, layer)
        self.data = None
        # Number of time slice required for finishing the transmission
        self.state = 0
        # if the wire is occupied
        self.is_occupied = False
        # if the wire is next to the end tile
        self.is_last = False
        self.end_tile_id = None

    def set_wire_task(self, wire_tasks):
        # Format:(end_tile_id, layer, x, y, length, is_last)
        self.state = wire_tasks[4]
        self.data = (wire_tasks[2], wire_tasks[3], wire_tasks[1])
        self.is_occupied = True
        self.is_last = wire_tasks[5]
        self.end_tile_id = wire_tasks[0]

    def update_time_slice(self):
        if self.is_occupied:
            self.state -= 1
            if self.state == 0:
                self.is_occupied = False
                if self.is_last:
                    # return data to update tile
                    return self.data
        return None
