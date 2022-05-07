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
                wire_postion = ((i, j), (i, j + 1))
                wire = BaseWire(wire_postion, band_width)
                self.wires.append(wire)
                self.wires_map[str(wire_postion)] = wire
        # vertically wire
        for j in range(tile_net_shape[1]):
            for i in range(tile_net_shape[0] - 1):
                wire_postion = ((i, j), (i + 1, j))
                wire = BaseWire(wire_postion, band_width)
                self.wires.append(wire)
                self.wires_map[str(wire_postion)] = wire

    def set_transparent_flag(self, transparent_flag):
        """
        set the transparent flag
        """
        for wire in self.wires:
            wire.set_transparent_flag(transparent_flag)