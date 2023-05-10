#-*-coding:utf-8-*-
"""
@FileName:
    linear_programming.py
@Description:
    add this file to support the linear programming for the schedule
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2023/05/09 18:14
"""
from typing import List
import numpy as np

from mnsim_noc.utils.component import Component
from mnsim_noc.Tile.base_tile import BaseTile
from mnsim_noc.Communication.base_communication import BaseCommunication
from mnsim_noc.Wire.wire_net import WireNet, _get_position_key, _get_map_key

def _get_index(_v, _d):
    """
    get index or set index to new value in dict
    """
    if _v not in _d:
        _d[_v] = len(_d)
    return _d[_v]

class ScheduleLinearProgramming(Component):
    """
    class of the linear programming for the schedule
    """
    REGISTRY = "schedule_linear_programming"
    NAME = "schedule_linear_programming"
    def __init__(self, communication_list: List[BaseCommunication], wire_net: WireNet):
        """
        init the linear programming based on the communication list and wire net
        """
        super(ScheduleLinearProgramming, self).__init__()
        # set up the params
        self._set_up_params(communication_list, wire_net)

    def _set_up_params(self, communication_list: List[BaseCommunication], wire_net: WireNet):
        # first, get the arc-node incidence matrix based on the adjacency dict
        this_adjacency_dict = wire_net.adjacency_dict
        # mapping dict is used to transfer the node str to node position (in tuple)
        this_mapping_dict = wire_net.mapping_dict
        # get M and E means the number of nodes and edges, respectively, init A matrix
        M = len(this_adjacency_dict)
        E = sum([len(v) for v in this_adjacency_dict.values()])
        A = np.zeros(shape=(M, E))
        # empty dict to store and index the node and edge (edge have 2 items)
        node_index_dict = {}
        edge_index_dict = {}
        for node_a, node_a_target in this_adjacency_dict.items():
            for node_b in node_a_target:
                # there is a edge from node_a to node_b
                node_index_a = _get_index(node_a, node_index_dict)
                node_index_b = _get_index(node_b, node_index_dict)
                edge = node_a + "->" + node_b
                edge_index = _get_index(edge, edge_index_dict)
                # set the A matrix
                A[node_index_a][edge_index] = 1
                A[node_index_b][edge_index] = -1
        # check for A
        assert (np.matmul(A, np.ones(shape=(E, 1))) == np.zeros(shape=(M, 1))).all(), \
            "the sum of arc-node incidence matrix row is not zero"
        assert (np.matmul(A.T, np.ones(shape=(M, 1))) == np.zeros(shape=(E, 1))).all(), \
            "the sum of arc-node incidence matrix column is not zero"
        # second, get the input matrix B for the supply and demand
        K = len(communication_list)
        B = np.zeros(shape=(M, K))
        for k, comm in enumerate(communication_list):
            input_tile: BaseTile  = comm.input_tile
            output_tile: BaseTile = comm.output_tile
            T_k = input_tile.total_amount_output_size
            node_start_index = node_index_dict[_get_position_key(input_tile.position)]
            node_end_index = node_index_dict[_get_position_key(output_tile.position)]
            B[node_start_index][k] = T_k
            B[node_end_index][k] = -T_k
        # check for the B matrix
        ones_M = np.ones(shape=(M, 1))
        zeros_K = np.zeros(shape=(K, 1))
        assert (np.matmul(B.T, ones_M) == zeros_K).all(), \
            "the sum of supply and demand is not zero"
        # third, get other parameters and equivalent path
        zeros_E_K = np.zeros(shape=(E, K))
        alpha, beta = 1, 1
        Cost = np.ones(shape=(E, 1))
        Value = np.ones(shape=(K, 1))
        E_extra = len(wire_net.wires)
        EP = np.zeros(shape=(E_extra, E))
        for wire_id, wire in enumerate(wire_net.wires):
            for edge_description, edge_id in edge_index_dict.items():
                # decide if the edge is running in this wire
                wire_description = _get_map_key(wire.wire_position)
                edge_description = edge_description.split("->")
                assert len(edge_description) == 2, \
                    "the edge description is not correct"
                edge_description = _get_map_key((
                    this_mapping_dict[edge_description[0]],
                    this_mapping_dict[edge_description[1]]
                ))
                if wire_description == edge_description:
                    EP[wire_id][edge_id] = 1
        assert (np.matmul(EP, np.ones(shape=(E, 1))) == 2*np.ones(shape=(E_extra, 1))).all(), \
            "the sum of equivalent path row must be 2"
        assert (np.matmul(EP.T, np.ones(shape=(E_extra, 1))) == np.ones(shape=(E, 1))).all(), \
            "the sum of equivalent path column must be 1"
        # transfer to the self members
        self.alpha, self.beta = alpha, beta
        self.C, self.V = Cost, Value
        self.EP, self.zeros_E_K = EP, zeros_E_K
        self.A, self.B = A, B
        self.M, self.E, self.K, self.E_extra = M, E, K, E_extra
