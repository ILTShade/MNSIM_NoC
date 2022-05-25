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
        self.transfer_time_range = {}

    def get_transfer_time(self, data_list):
        """
        get the transfer time
        """
        data_size = sum([get_data_size(data) for data in data_list])
        return data_size / self.band_width

    def set_wire_state(self, wire_state, communication_id, current_time):
        """
        set the wire state
        """
        # add the transfer time range
        if communication_id not in self.transfer_time_range:
            self.transfer_time_range[communication_id] = []
        if wire_state == True:
            # add new range
            self.transfer_time_range[communication_id].append([current_time])
        else:
            # add end time
            self.transfer_time_range[communication_id][-1].append(current_time)
        if self.transparent_flag:
            return None
        assert wire_state != self.running_state
        self.running_state = wire_state
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

    def get_running_rate(self, end_time):
        """
        get the running rate
        """
        transfer_total_time = 0.
        for _, value in self.transfer_time_range.items():
            transfer_total_time += sum([end-start for start, end in value])
        return transfer_total_time * 1. / end_time
