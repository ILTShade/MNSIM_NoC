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
        # 正在传输的数据(在特征图上坐标及特征图层数)
        self.data = None
        # 剩余传输任务占用时间片数
        self.state = 0
        # 是否被占用
        self.is_occupied = False
        # Wire是否将数据传入end_tile
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
                    # 返回数据以更新Tile
                    return self.data
        return None
