#-*-coding:utf-8-*-
"""
@FileName:
    time_slice_tile.py
@Description:
    Array class for time slice
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2021/10/08 18:28
"""
from mnsim_noc.Array import BaseArray

class TimeSliceArray(BaseArray):
    NAME = "time_slice_array"

    def __init__(self, array_cfg, total_task, scheduler, router, time_slice):
        super().__init__(self, array_cfg, total_task, scheduler, router)
        self.time_slice = time_slice
        self.tile_dict = dict()
        self.wire_dict = dict()

    def task_assignment(self):
        pass

    def check_finish(self):
        return True

    def set_wire_task(self, routing_result):
        pass

    def update_tile(self):
        pass

    def run(self):
        # task assignment
        self.task_assignment()
        # run for every slice
        while True:
            if self.check_finish():
                break
            # 0, all tile and wire update for one slice
            for tile_id, tile in self.tile_dict.items():
                tile.update_time_slice()
            for wire_id, wire in self.wire_dict.items():
                wire.update_time_slice()
            # 1, update tile input and output
            self.update_tile()
            # 2, get all transfer data
            transfer_data = dict()
            for tile_id, tile in self.tile_dict.items():
                transfer_data[tile_id] = tile.update_output()
            # 3, get all wire state
            wire_state = dict()
            for wire_id, wire in self.wire_dict.items():
                wire_state[wire_id] = wire.state
            # 4, routing
            routing_result = self.router.assign(transfer_data, wire_state)
            # 5, set wire task
            self.set_wire_task(routing_result)