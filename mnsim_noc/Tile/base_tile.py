# -*-coding:utf-8-*-
"""
@FileName:
    base_tile.py
@Description:
    Base Tile class for time slice
@CreateTime:
    2021/10/08 17:57
"""
from abc import abstractmethod
from mnsim_noc import Component


class BaseTile(Component):
    REGISTRY = "tile"

    def __init__(self, position, task_cfg):
        super().__init__()
        # input and output data
        # format: (start_tile_id, end_tile_id, layer, x, y, length)
        self.position = position
        self.task_cfg = task_cfg
        self.tile_id = BaseTile.get_tile_id(position)
        # format: (x,y) on input/output feature map
        self.input_list = []
        self.output_list = []
        # Number of time slice required for computing the next output
        self.state = 0

    @classmethod
    def get_tile_id(cls, position):
        return "{}_{}".format(position[0], position[1])

    @abstractmethod
    def update_input(self, inputs):
        pass

    @abstractmethod
    def update_time_slice(self):
        pass

    @abstractmethod
    def get_output(self):
        pass

    @abstractmethod
    def update_output(self, outputs):
        pass
