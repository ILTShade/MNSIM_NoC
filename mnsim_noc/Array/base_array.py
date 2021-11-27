#-*-coding:utf-8-*-
"""
@FileName:
    base_time_slice_array.py
@Description:
    Base Array class
@CreateTime:
    2021/10/08 18:21
"""

from abc import abstractmethod
from mnsim_noc import Component


class BaseArray(Component):
    REGISTRY = "array"

    def __init__(self, tcg_mapping):
        super().__init__()
        self.tcg_mapping = tcg_mapping
        self.tcg_mapping.mapping_net()
        self.tcg_mapping.calculate_transfer_distance()
        # self.total_task = total_task
        # self.scheduler = scheduler
        self.router = None

    @abstractmethod
    def task_assignment(self):
        pass

    @abstractmethod
    def get_timeslice_num(self):
        pass

    @abstractmethod
    def run(self):
        pass
