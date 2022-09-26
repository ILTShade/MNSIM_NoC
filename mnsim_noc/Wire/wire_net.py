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
import copy
import numpy as np
from mnsim_noc.utils.component import Component
from mnsim_noc.Wire.base_wire import BaseWire

def _get_map_key(wire_position):
    """
    wire position, tuple of tuple
    like: ((0, 0), (0, 1))
    """
    if wire_position[0][0] + wire_position[0][1] > \
        wire_position[1][0] + wire_position[1][1]:
        return str((wire_position[1], wire_position[0]))
    return str(wire_position)

def _get_position_key(tile_position):
    """
    str the tile position like: (0, 0)
    """
    return str(tile_position)

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
        self.tile_net_shape = tile_net_shape
        self.wires = []
        self.wires_map = {}
        # wires topology and adjacency dict
        self.wires_topology = []
        self.adjacency_dict = {}
        self.origin_adjacency_dict = {} # the base adjacency dict, will NOT change
        self.mapping_dict = {}
        self.cache_static_path = {}
        # horizontally wire as usual
        for i in range(tile_net_shape[0]):
            for j in range(tile_net_shape[1] - 1):
                wire_position = ((i, j), (i, j + 1))
                wire = BaseWire(wire_position, band_width)
                self.wires.append(wire)
                self.wires_map[_get_map_key(wire_position)] = wire
                self.wires_topology.append(wire_position)
        # vertically wire as usual
        for j in range(tile_net_shape[1]):
            for i in range(tile_net_shape[0] - 1):
                wire_position = ((i, j), (i + 1, j))
                wire = BaseWire(wire_position, band_width)
                self.wires.append(wire)
                self.wires_map[_get_map_key(wire_position)] = wire
                self.wires_topology.append(wire_position)
        self.transparent_flag = False
        # init adjacency dict
        # IT SHOULD BE NOTICED THAT
        # all path are defined based on the wires_topology
        self._init_adjacency_dict(self.wires_topology)

    def _init_adjacency_dict(self, wires_topology):
        """
        init adjacency dict
        """
        # all wires in topology are linked
        self.adjacency_dict = {}
        self.mapping_dict = {}
        for wire_position in wires_topology:
            assert len(wire_position) == 2, \
                f"wire_position: {wire_position}, must be a tuple of tuple"
            # node a and node b are the two ends of the wire
            node_a = _get_position_key(wire_position[0])
            node_b = _get_position_key(wire_position[1])
            # add to the adjacency dict
            self.adjacency_dict[node_a] = self.adjacency_dict.get(node_a, []) + [node_b]
            self.adjacency_dict[node_b] = self.adjacency_dict.get(node_b, []) + [node_a]
            # add node a and node b to mapping
            if node_a not in self.mapping_dict:
                self.mapping_dict[node_a] = wire_position[0]
            else:
                assert self.mapping_dict[node_a] == wire_position[0]
            if node_b not in self.mapping_dict:
                self.mapping_dict[node_b] = wire_position[1]
            else:
                assert self.mapping_dict[node_b] == wire_position[1]
        # init origin adjacency dict
        self.origin_adjacency_dict = copy.deepcopy(self.adjacency_dict)

    def _update_adjacency_dict(self, wire:BaseWire, state):
        """
        whenever a wire is set state, update the adjacency dict
        """
        if wire.transparent_flag:
            # in case of transparent wire, do nothing
            return None
        # if state is true, remove the link from adjacency dict
        wire_position = wire.wire_position
        node_a = _get_position_key(wire_position[0])
        node_b = _get_position_key(wire_position[1])
        if state:
            self.adjacency_dict[node_a].remove(node_b)
            self.adjacency_dict[node_b].remove(node_a)
        else:
            self.adjacency_dict[node_a].append(node_b)
            self.adjacency_dict[node_b].append(node_a)
        return None

    def find_data_path(self, start_position, end_position, dynamic_flag):
        """
        find the data path from start_position to end_position
        start_position: tuple -> (row_index, column_index)
        end_position: tuple -> (row_index, column_index)
        dynamic_flag: bool -> for static path or dynamic path
        """
        # for dynamic and static, the adjacency dict is different
        if dynamic_flag is True:
            this_adjacency_dict = self.adjacency_dict
        else:
            # check for cache
            cache_key = _get_map_key((start_position, end_position))
            if cache_key in self.cache_static_path:
                return self.cache_static_path[cache_key]
            this_adjacency_dict = self.origin_adjacency_dict
        # init the start node and end node
        start_node, end_node = _get_position_key(start_position), _get_position_key(end_position)
        # init all node info list, and add the first start node
        all_node_info = {}
        for node, _ in this_adjacency_dict.items():
            # the first item in list is distance from start_node, None for not reach
            # the second is the previous node
            all_node_info[node] = [None, None]
        assert start_node in all_node_info and end_node in all_node_info, \
            f"start_node and end_node should be in all_node_info"
        all_node_info[start_node][0] = 0
        # traverse the graph
        add_node_list = [start_node]
        path_flag = False
        while True:
            next_node_list = []
            # get the next hops node
            for node in add_node_list:
                adjacency_node_list = this_adjacency_dict[node]
                for adjacency_node in adjacency_node_list:
                    if all_node_info[adjacency_node][0] is not None:
                        continue
                    # add to next node list
                    all_node_info[adjacency_node] = [all_node_info[node][0] + 1, node]
                    next_node_list.append(adjacency_node)
            # check for output
            if end_node in next_node_list:
                # find end node, break
                path_flag = True
                break
            if len(next_node_list) == 0:
                # no new node, break
                path_flag = False
                break
            add_node_list = next_node_list
        # get path if path is found
        output_path = None
        if path_flag is True:
            # get total path
            path = []
            current_node = end_node
            while True:
                path.append(self.mapping_dict[current_node])
                if current_node == start_node:
                    break
                current_node = all_node_info[current_node][1]
            output_path = [(path[i], path[i+1]) for i in range(len(path)-1)] # get wire path
        # for dynamic and static, the output is different
        if dynamic_flag is True:
            return output_path
        assert output_path is not None, f"output_path should not be None"
        self.cache_static_path[cache_key] = output_path
        return self.cache_static_path[cache_key]

    def set_transparent_flag(self, transparent_flag):
        """
        set the transparent flag
        """
        for wire in self.wires:
            wire.set_transparent_flag(transparent_flag)
        self.transparent_flag = transparent_flag

    def get_data_path_state(self, transfer_path):
        """
        get data path state
        return False only when all wires are idle
        """
        all_state = [self.wires_map[_get_map_key(path)].get_wire_state()
            for path in transfer_path
        ]
        return any(all_state)

    def set_data_path_state(self, transfer_path, state, communication_id, current_time):
        """
        set data path state, and record transfer range time
        """
        for path in transfer_path:
            wire = self.wires_map[_get_map_key(path)]
            wire.set_wire_state(state, communication_id, current_time)
            self._update_adjacency_dict(wire, state)

    def get_wire_transfer_time(self, transfer_path, data_list):
        """
        get wire transfer time
        """
        transfer_time = 0
        for path in transfer_path:
            wire = self.wires_map[_get_map_key(path)]
            transfer_time += wire.get_transfer_time(data_list)
        return transfer_time

    def check_finish(self):
        """
        check if all wires are idle
        """
        for wire in self.wires:
            assert wire.get_wire_state() is False

    def get_running_rate(self, end_time):
        """
        show wire rate, two decimal places
        """
        horizontal_rate = np.zeros(
            [self.tile_net_shape[0], self.tile_net_shape[1] - 1]
        )
        for i in range(self.tile_net_shape[0]):
            for j in range(self.tile_net_shape[1] - 1):
                wire_position = ((i, j), (i, j + 1))
                horizontal_rate[i, j] = \
                    self.wires_map[_get_map_key(wire_position)].get_running_rate(end_time)
        vertical_rate = np.zeros(
            [self.tile_net_shape[0] - 1, self.tile_net_shape[1]]
        )
        for i in range(self.tile_net_shape[0] - 1):
            for j in range(self.tile_net_shape[1]):
                wire_position = ((i, j), (i + 1, j))
                vertical_rate[i, j] = \
                    self.wires_map[_get_map_key(wire_position)].get_running_rate(end_time)
        return horizontal_rate, vertical_rate

    def get_wire_range(self):
        """
        get wire range for all of the wire
        """
        wire_range_list = []
        for key, item in self.wires_map.items():
            wire_range = item.wire_range
            if len(wire_range) == 0:
                continue
            wire_range_list.append({
                "wire_position": key,
                "range": wire_range,
            })
        return wire_range_list

    def get_communication_amounts(self):
        """
        get communication amounts on all of the wire
        """
        communication_amounts = 0.
        for wire in self.wires:
            communication_amounts += wire.get_communication_amounts()
        return communication_amounts
