#-*-coding:utf-8-*-
"""
@FileName:
    wire_net.py
@Description:
    wire net class for behavior-driven simulation
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 17:20
"""
from mnsim_noc.utils.component import Component
from mnsim_noc.Wire.base_wire import BaseWire

class WireNet(Component):
    """
    wire net class for behavior-driven simulation
    """
    REGISTRY = "wire_net"
    NAME = "behavior_driven"
    def __init__(self, tile_net_shape, band_width):
        """
        wire net
        tile_net_shape: tuple -> (row_num, column_num)
        """
        super(WireNet, self).__init__()
        # init wire net
        self.wires = []
        self.wires_map = {}
        # horizontally wire
        for i in range(tile_net_shape[0]):
            for j in range(tile_net_shape[1] - 1):
                wire_position = ((i, j), (i, j + 1))
                wire = BaseWire(wire_position, band_width)
                self.wires.append(wire)
                self.wires_map[self._get_map_key(wire_position)] = wire
        # vertically wire
        for j in range(tile_net_shape[1]):
            for i in range(tile_net_shape[0] - 1):
                wire_position = ((i, j), (i + 1, j))
                wire = BaseWire(wire_position, band_width)
                self.wires.append(wire)
                self.wires_map[self._get_map_key(wire_position)] = wire

    def _get_map_key(self, wire_position):
        """
        wire position, tuple of tuple
        like: ((0, 0), (0, 1))
        """
        if wire_position[0][0] + wire_position[0][1] > \
            wire_position[1][0] + wire_position[1][1]:
            return str((wire_position[1], wire_position[0]))
        return str(wire_position)

    def set_transparent_flag(self, transparent_flag):
        """
        set the transparent flag
        """
        for wire in self.wires:
            wire.set_transparent_flag(transparent_flag)

    def get_data_path_state(self, transfer_path):
        """
        get data path state
        return False only when all wires are idle
        """
        all_state = [self.wires_map[self._get_map_key(path)].get_wire_state()
            for path in transfer_path
        ]
        return any(all_state)

    def set_data_path_state(self, transfer_path, state):
        """
        set data path state
        """
        for path in transfer_path:
            self.wires_map[self._get_map_key(path)].set_wire_state(state)

    def get_wire_transfer_time(self, transfer_path, data_list, current_time):
        """
        get wire transfer time
        """
        transfer_end_time = current_time
        for path in transfer_path:
            wire = self.wires_map[self._get_map_key(path)]
            transfer_end_time += wire.get_transfer_time(data_list)
        return transfer_end_time

    def check_finish(self):
        """
        check if all wires are idle
        """
        for wire in self.wires:
            assert wire.get_wire_state() == False
