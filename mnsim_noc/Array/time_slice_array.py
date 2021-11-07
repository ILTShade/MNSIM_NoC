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
import re
from mnsim_noc.Array import BaseArray


class TimeSliceArray(BaseArray):
    NAME = "time_slice_array"

    def __init__(self, array_cfg, total_task, scheduler, router, time_slice):
        super().__init__(self, array_cfg, total_task, scheduler, router)
        self.time_slice = time_slice
        self.tile_dict = dict()
        self.wire_dict = dict()
        self.wire_data_transferred = dict()

    def task_assignment(self):
        pass

    def check_finish(self):
        for tile_id, tile in self.tile_dict.items():
            if tile.input_list or tile.output_list:
                return False
        for wire_id, wire in self.wire_dict.items():
            if wire.state:
                return False
        return True

    def set_wire_task(self, routing_result):
        # task format: (x, y, end_tile_id, length, layer, is_first, is_last)
        # path format: (list[occupied_wire_id], (x, y, end_tile_id, length, layer_out))
        for path in routing_result:
            wire_list = path[0]
            path_data = path[1]
            wire_len = len(wire_list)
            for index, wire_id in enumerate(wire_list):
                is_first = (index == 0)
                is_last = (index == wire_len-1)
                self.wire_dict[wire_id].set_wire_task(path_data + (is_first, is_last))

    def update_tile(self):
        for wire_id, wire_data in self.wire_data_transferred.items():
            if wire_data:
                # wire_data format: (x, y, end_tile_id, layer, is_first, is_last)
                if wire_data[4]:
                    wire_position = tuple(map(int, re.findall(r"\d+", wire_id)))
                    tile_id = "{}_{}".format(wire_position[0], wire_position[1])
                    self.tile_dict[tile_id].update_output([wire_data[0:3]])
                if wire_data[5]:
                    tile_id = wire_data[2]
                    self.tile_dict[tile_id].update_input([wire_data[0:2]+wire_data[3]])

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
            # get the data transferred by wires
            self.wire_data_transferred = dict()
            for wire_id, wire in self.wire_dict.items():
                self.wire_data_transferred[wire_id] = wire.update_time_slice()
            # 1, update tile input and output
            self.update_tile()
            # 2, get all transfer data
            transfer_data = dict()
            for tile_id, tile in self.tile_dict.items():
                # transfer_data format: (x, y, end_tile_id, length, layer_out)
                transfer_data[tile_id] = tile.get_output()
            # 3, get all wire state
            wire_state = dict()
            for wire_id, wire in self.wire_dict.items():
                wire_state[wire_id] = wire.state
            # 4, routing
            # path format: (list[occupied_wire_id], (x, y, end_tile_id, length, layer_out))
            routing_result = self.router.assign(transfer_data, wire_state)
            # 5, set wire task
            self.set_wire_task(routing_result)
