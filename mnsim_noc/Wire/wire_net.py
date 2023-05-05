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
from queue import PriorityQueue

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

def _mesh_heuristic(x_dis, _, y_dis, __):
    """
    mesh heuristic
    """
    return x_dis + y_dis

def _torus_heuristic(x_dis, x_len, y_dis, y_len):
    """
    torus heuristic
    """
    return min(x_dis, x_len - x_dis) + min(y_dis, y_len - y_dis)

class _MyPriorityQueue(PriorityQueue):
    """
    add a counter to the PriorityQueue
    """
    def __init__(self, *args, **kwargs):
        super(_MyPriorityQueue, self).__init__(*args, **kwargs)
        self.counter = 0
    def put(self, item, block=True, timeout=None):
        """
        put item with priority
        """
        super(_MyPriorityQueue, self).put((item[0], self.counter, item[1]), block, timeout)
        self.counter += 1
    def get(self, block=True, timeout=None):
        """
        get item with priority
        """
        _, _, item = super(_MyPriorityQueue, self).get(block, timeout)
        return item
    def clear(self):
        """
        clear the queue
        """
        self.queue.clear()
        self.counter = 0


class WireNet(Component):
    """
    wire net class for behavior-driven simulation
    """
    REGISTRY = "wire_net"
    NAME = "behavior_driven"
    def __init__(self, tile_net_shape, band_width, noc_topology):
        """
        wire net
        tile_net_shape: tuple -> (row_num, column_num)
        """
        super(WireNet, self).__init__()
        # init wire net, list and dict of wires
        # the same instances, different references
        self.tile_net_shape = tile_net_shape
        self.wires = []
        self.wires_map = {}
        # wires topology and adjacency dict
        self.wires_topology = []
        self.adjacency_dict = {}
        self.origin_adjacency_dict = {} # the base adjacency dict, will NOT change
        self.mapping_dict = {}
        # horizontally wire as usual
        assert noc_topology in ["mesh", "torus"], \
            f"noc_topology: {noc_topology}, must be mesh or torus"
        def _construct_add_wire(wire_position):
            """
            construct and add wire
            """
            wire = BaseWire(wire_position, band_width)
            self.wires.append(wire)
            self.wires_map[_get_map_key(wire_position)] = wire
            self.wires_topology.append(wire_position)
        for i in range(tile_net_shape[0]):
            for j in range(tile_net_shape[1] - 1):
                wire_position = ((i, j), (i, j + 1))
                _construct_add_wire(wire_position)
            # add for torus
            if noc_topology == "torus":
                wire_position = ((i, tile_net_shape[1] - 1), (i, 0))
                _construct_add_wire(wire_position)
        # vertically wire as usual
        for j in range(tile_net_shape[1]):
            for i in range(tile_net_shape[0] - 1):
                wire_position = ((i, j), (i + 1, j))
                _construct_add_wire(wire_position)
            # add for torus
            if noc_topology == "torus":
                wire_position = ((tile_net_shape[0] - 1, j), (0, j))
                _construct_add_wire(wire_position)
        # set function
        self._heuristic_core = _mesh_heuristic if noc_topology == "mesh" else _torus_heuristic
        self.transparent_flag = False
        # init adjacency dict, all path are defined based on the wires_topology
        self._init_adjacency_dict(self.wires_topology)
        # set the base instance for the breadth first search
        self.frontier = _MyPriorityQueue()
        self.came_from = dict()
        self.cost_so_far = dict()
        # cache
        self.adaptive_cache_dict = dict()

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

    def _init_bfs(self):
        """
        init the bfs
        frontier, came_from, cost_so_far
        """
        self.frontier.clear()
        for key, _ in self.mapping_dict.items():
            self.came_from[key] = None
            self.cost_so_far[key] = float("inf")

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

    def _xy_routing_path(self, start_position, end_position, order="row"):
        """
        find the data path from start_position to end_position based on X-Y routing
        without crossing the border
        start_position: tuple -> (row_index, column_index)
        end_position: tuple -> (row_index, column_index)
        """
        # row for in X dimension first, and Y dimension second
        # col for in Y dimension first, and X dimension second
        if order == "row":
            # in each element, the first is the index of the position
            # and the second is the shift
            operations = [(1, (0, 1)), (0, (1, 0))]
        elif order == "col":
            operations = [(0, (1, 0)), (1, (0, 1))]
        else:
            raise ValueError(f"order: {order}, must be row or col")
        # find the path based on the operations
        path = [start_position]
        current_position = start_position
        for index, shift in operations:
            # first, set the shift
            if end_position[index] == current_position[index]:
                continue
            if end_position[index] < current_position[index]:
                shift = (-shift[0], -shift[1])
            while True:
                current_position = (current_position[0] + shift[0], current_position[1] + shift[1])
                path.append(current_position)
                if current_position[index] == end_position[index]:
                    break
        return path

    def _winding_routing_path(self, start_position, end_position, order="row"):
        """
        find the data path from start_position to end_position based on winding routing
        without crossing the border
        start_position: tuple -> (row_index, column_index)
        end_position: tuple -> (row_index, column_index)
        """
        operations = [(1, (0, 1)), (0, (1, 0))] # base operations
        if order == "row":
            choice = 1 - 0
        elif order == "col":
            choice = 1 - 1
        else:
            raise ValueError(f"order: {order}, must be row or col")
        # find the path based on the operations and choice
        path_length_list = []
        path = [start_position]
        current_position = start_position
        while True:
            # in the start of every loop, change the choice
            choice = 1 - choice
            # initialize the path length list, and check if the path is changed
            path_length_list.append(len(path))
            if len(path_length_list) >= 3 and \
                path_length_list[-1] == path_length_list[-2] == path_length_list[-3]:
                # if the path length is not changed for three times, stop
                break
            # first, get the index and shift
            index, shift = operations[choice]
            if end_position[index] == current_position[index]:
                continue
            if end_position[index] < current_position[index]:
                # change the shift
                shift = (-shift[0], -shift[1])
            while True:
                next_position = (current_position[0] + shift[0], current_position[1] + shift[1])
                state = self.wires_map[
                    _get_map_key((current_position, next_position))
                ].get_wire_state()
                if state:
                    break
                current_position = next_position
                path.append(current_position)
                if current_position[index] == end_position[index]:
                    break
        # check if can find the path
        if path[-1] == end_position:
            return path
        return None

    def _west_first_routing_path(self, start_position, end_position):
        """
        find the data path based on west first routing
        """
        # end on the left of the start
        if end_position[1] <= start_position[1]:
            return self._xy_routing_path(start_position, end_position, order="row")
        return self._winding_routing_path(start_position, end_position, order="row")

    def _north_last_routing_path(self, start_position, end_position):
        """
        find the data path based on north last routing
        """
        # end on the top of the start
        if end_position[0] <= start_position[0]:
            return self._xy_routing_path(start_position, end_position, order="row")
        return self._winding_routing_path(start_position, end_position, order="row")

    def _negative_first_routing_path(self, start_position, end_position):
        """
        find the data path based on negative first routing
        """
        # end on the left of the start
        if end_position[0] <= start_position[0] and end_position[1] <= start_position[1]:
            return self._xy_routing_path(start_position, end_position, order="row")
        if end_position[0] > start_position[0] and end_position[1] > start_position[1]:
            return self._xy_routing_path(start_position, end_position, order="col")
        return self._winding_routing_path(start_position, end_position, order="row")

    def _heuristic_distance(self, current_node, end_node):
        """
        calculate the heuristic distance between current node and end node
        """
        current_position = self.mapping_dict[current_node]
        end_position = self.mapping_dict[end_node]
        # calculate the heuristic distance
        x_dis = abs(end_position[1] - current_position[1])
        y_dis = abs(end_position[0] - current_position[0])
        return self._heuristic_core(x_dis, self.tile_net_shape[1], y_dis, self.tile_net_shape[0])

    def _get_path_based_came_from(self, start_node, end_node):
        """
        get the path from start node to end node based on came_from
        """
        if self.came_from[end_node] is None:
            return None
        path = [end_node]
        current_node = end_node
        while current_node != start_node:
            current_node = self.came_from[current_node]
            path.append(current_node)
        path.reverse()
        path = [self.mapping_dict[node] for node in path]
        return path

    def _greedy_best_first_routing_path(self, start_position, end_position, this_adjacency_dict):
        """
        find the data path based on greedy best first routing
        """
        # get start and end node, and init the queue, came_from
        start_node, end_node = _get_position_key(start_position), _get_position_key(end_position)
        self._init_bfs()
        self.frontier.put((0, start_node))
        self.came_from[start_node] = "null"
        # get the node with highest priority
        while not self.frontier.empty():
            current_node = self.frontier.get()
            if current_node == end_node:
                # break when reach the end node
                break
            # get the neighbors of current node
            for neighbor in this_adjacency_dict[current_node]:
                if self.came_from[neighbor] is None:
                    # calculate the priority
                    priority = self._heuristic_distance(neighbor, end_node)
                    self.frontier.put((priority, neighbor))
                    self.came_from[neighbor] = current_node
        # get the path from came_from
        path = self._get_path_based_came_from(start_node, end_node)
        return path

    def _breadth_first_routing_path(
            self, start_position, end_position, this_adjacency_dict, priority_func
        ):
        """
        find the data path based on breadth first routing
        """
        # get start and end node, and init the queue, came_from and cost_so_far
        start_node, end_node = _get_position_key(start_position), _get_position_key(end_position)
        self._init_bfs()
        self.frontier.put((0, start_node))
        self.came_from[start_node] = None
        self.cost_so_far[start_node] = 0
        # get the node with highest priority
        while not self.frontier.empty():
            current_node = self.frontier.get()
            if current_node == end_node:
                # break when reach the end node
                break
            # get the neighbors of current node
            for neighbor in this_adjacency_dict[current_node]:
                neighbor_cost = self.cost_so_far[current_node] + 1
                if neighbor_cost < self.cost_so_far[neighbor]:
                    self.cost_so_far[neighbor] = neighbor_cost
                    priority = neighbor_cost + priority_func(neighbor, end_node)
                    self.frontier.put((priority, neighbor))
                    self.came_from[neighbor] = current_node
        # get the path from came_from
        path = self._get_path_based_came_from(start_node, end_node)
        return path

    def _adaptive_routing_path(self, start_position, end_position):
        """
        find the data path based on adaptive routing (X-Y, support for mesh and torus)
        """
        cache_key = _get_map_key((start_position, end_position))
        if cache_key not in self.adaptive_cache_dict:
            self.adaptive_cache_dict[cache_key] = self._breadth_first_routing_path(
                start_position, end_position, self.origin_adjacency_dict, lambda x, y: 0
            )
        return self.adaptive_cache_dict[cache_key]

    def _greedy_routing_path(self, start_position, end_position):
        """
        find the data path based on greedy routing
        """
        return self._greedy_best_first_routing_path(
            start_position, end_position, self.adjacency_dict
        )

    def _dijkstra_routing_path(self, start_position, end_position):
        """
        find the data path based on dijkstra routing
        """
        return self._breadth_first_routing_path(
            start_position, end_position, self.adjacency_dict, lambda x, y: 0
        )

    def _astar_routing_path(self, start_position, end_position):
        """
        find the data path based on astar routing
        """
        return self._breadth_first_routing_path(
            start_position, end_position, self.adjacency_dict, self._heuristic_distance
        )

    def find_data_path_cate(self, start_position, end_position, cate):
        """
        find the data path from start_position to end_position_list
        start_position: tuple -> (row_index, column_index)
        end_position: tuple -> (row_index, column_index)
        cate: str -> different path generator, "naive", "adaptive" and so on
        """
        # this function is the decorator of _find_data_path function
        if cate == "naive":
            return self._xy_routing_path(start_position, end_position, "row")
        if cate == "west_first":
            return self._west_first_routing_path(start_position, end_position)
        if cate == "north_last":
            return self._north_last_routing_path(start_position, end_position)
        if cate == "negative_first":
            return self._negative_first_routing_path(start_position, end_position)
        if cate == "adaptive":
            return self._adaptive_routing_path(start_position, end_position)
        if cate == "greedy":
            return self._greedy_routing_path(start_position, end_position)
        if cate == "dijkstra":
            return self._dijkstra_routing_path(start_position, end_position)
        if cate == "astar":
            return self._astar_routing_path(start_position, end_position)
        raise ValueError(f"cate should be support cates but get {cate}")

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
        all_state = [
            self.wires_map[
                _get_map_key((transfer_path[i], transfer_path[i+1]))
            ].get_wire_state()
            for i in range(len(transfer_path)-1)
        ]
        return any(all_state)

    def set_data_path_state(self, transfer_path, state, communication_id, current_time):
        """
        set data path state, and record transfer range time
        """
        for i in range(len(transfer_path)-1):
            path = (transfer_path[i], transfer_path[i+1])
            wire = self.wires_map[_get_map_key(path)]
            wire.set_wire_state(state, communication_id, current_time)
            self._update_adjacency_dict(wire, state)

    def get_wire_transfer_time(self, transfer_path, data_list):
        """
        get wire transfer time
        """
        transfer_time = 0.
        for i in range(len(transfer_path)-1):
            path = (transfer_path[i], transfer_path[i+1])
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
        # only for mesh, not for torus
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
