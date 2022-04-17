# -*-coding:utf-8-*-
"""
@FileName:
    no_conflicts_wire.py
@Description:
    Wire Class for time slice without conflicts
@CreateTime:
    ---
"""
from mnsim_noc.Wire import BaseWire


class NoConflictsWire(BaseWire):
    NAME = "no_conflicts_wire"

    def __init__(self, position):
        super().__init__(position)
        # data set transmitted on the wire
        # format: [state,(x, y, end_tile_id, layer, is_first, is_last)]
        # state: Number of time slice required to finish the transmission
        self.data = []
        # data transferred during simulation
        self.transferred_data = 0

    def set_wire_task(self, wire_tasks, wait_time):
        # Format:(x, y, end_tile_id, length, layer, is_first, is_last)
        self.data.append([int(wire_tasks.length)+int(wait_time),wire_tasks])

    def update_time_slice(self, n):
        # Format: list[(x, y, end_tile_id, layer, is_first, is_last)]
        tmp_data = []
        for index, single_data in enumerate(self.data):
            if single_data[0] > 0:
                self.data[index][0] -= n
        for single_data in self.data[:]:
            if single_data[0] == 0:
                tmp_data.append(single_data[1])
                self.data.remove(single_data)
        return tmp_data

    def get_roofline(self):
        # no need for roofline
        pass

    def get_wait_time(self):
        # get the end time of occupation
        pass
    
    def get_timeslice_num(self):
        # get the next timeslice num
        tmp_timeslice_num = float("inf")
        for single_data in self.data:
            tmp_timeslice_num =  min(max(1,single_data[0]), tmp_timeslice_num)
        return tmp_timeslice_num

    def check_finish(self):
        if self.data:
            return False
        else:
            return True