#-*-coding:utf-8-*-
"""
@FileName:
    time_slice_router.py
@Description:
    Router class for time slice
@CreateTime:
    2021/10/22 16:00
"""
from mnsim_noc.Router import BaseRouter


class TimeSliceRouter(BaseRouter):
    NAME = "time_slice_tile"

    def __init__(self):
        super().__init__(self)

    def assign(self, transfer_data, wire_state):
        pass
