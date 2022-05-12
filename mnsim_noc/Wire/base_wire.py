# -*-coding:utf-8-*-
"""
@FileName:
    base_wire.py
@Description:
    Base Wire Class for behavior-driven simulation
@CreateTime:
    2021/10/08 18:17
"""
from mnsim_noc.utils.component import Component
from mnsim_noc.Buffer.base_buffer import get_data_size

class BaseWire(Component):
    """
    Base Wire Class for bahahavior-driven simulation
    position: tuple -> (start, end)
        start, end -> (row, column)
    """
    REGISTRY = "wire"
    NAME = "behavior_driven"
    def __init__(self, wire_position, band_width):
        super(BaseWire, self).__init__()
        self.wire_position = wire_position
        self.band_width = band_width
        self.running_state = False
        self.transparent_flag = False
        self.transfer_time_range = []

    def get_transfer_time(self, data_list):
        """
        get the transfer time
        """
        data_size = sum([get_data_size(data) for data in data_list])
        return data_size / self.band_width

    def set_wire_state(self, wire_state, current_time):
        """
        set the wire state
        """
        if self.transparent_flag:
            return None
        assert wire_state != self.running_state
        self.running_state = wire_state
        if wire_state == True:
            # add new range
            self.transfer_time_range.append([current_time])
        else:
            # add end time
            self.transfer_time_range[-1].append(current_time)
        return None

    def get_wire_state(self):
        """
        get the wire state
        """
        if self.transparent_flag:
            return False
        return self.running_state

    def set_transparent_flag(self, transparent_flag):
        """
        set the transparent flag
        """
        self.transparent_flag = transparent_flag
