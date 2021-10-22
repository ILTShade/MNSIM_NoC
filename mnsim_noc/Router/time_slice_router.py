#-*-coding:utf-8-*-
"""
@FileName:
    time_slice_router.py
@Description:
    Router class for time slice
@CreateTime:
    2021/10/22 16:00
"""
import re
from mnsim_noc.Router import BaseRouter


class TimeSliceRouter(BaseRouter):
    NAME = "time_slice_tile"

    def __init__(self):
        super().__init__(self)
        # 规划好的路径
        # Format: (start_tile_id, end_tile_id, list[occupied_wire_id])
        self.paths = []

    def assign(self, transfer_data, wire_state):
        # transfer_data: dict()[tile_id->tile.output]
        # wire_state: dict()[wire_id->wire.state]
        for start_tile_id in transfer_data:
            # 提取起点与终点id中的位置信息
            start_tile_position = tuple(map(int, re.findall(r"\d+", start_tile_id)))
            end_tile_position = tuple(map(int, re.findall(r"\d+", transfer_data[start_tile_id][2])))
            step_x = end_tile_position[0]-start_tile_position[0]
            step_y = end_tile_position[1]-start_tile_position[1]
            for i in range(1, step_x+step_y):
                # TODO:实现路径的搜索与选择
                # 遍历所有可行路径
                # 维护第i次遍历时的可行路径集合
                pass
        pass
