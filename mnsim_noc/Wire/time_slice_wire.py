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
        super.__init__(self, position)
        # 正在传输的数据(在特征图上坐标及特征图层数)
        self.data = None
        # 剩余占用时间片数
        self.time = 0
        # 是否被占用
        self.is_occupied = False
        # Wire是否将数据传入end_tile
        self.is_last = False
        self.end_tile_id = None

    def set_wire_task(self, wire_tasks):
        # Format:(end_tile_id, layer, x, y, length, is_last)
        self.time = wire_tasks[4]
        self.data = (wire_tasks[2], wire_tasks[3], wire_tasks[1])
        self.is_occupied = True
        self.is_last = wire_tasks[5]
        self.end_tile_id = wire_tasks[0]

    def update_time_slice(self):
        if self.is_occupied:
            self.time -= 1
            if self.time == 0:
                if self.is_last:
                    # TODO:更新对应Tile的输入列表
                    pass
                self.is_occupied = False
