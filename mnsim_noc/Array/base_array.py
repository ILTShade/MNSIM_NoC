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

    def __init__(self, array_cfg, total_task, scheduler, router):
        self.array_cfg = array_cfg
        self.total_task = total_task
        self.scheduler = scheduler
        self.router = router

    @abstractmethod
    def task_assignment(self):
        pass

    @abstractmethod
    def run(self):
        pass
