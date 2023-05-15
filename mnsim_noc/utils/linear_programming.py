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
import copy
from typing import List

import cvxpy as cp
import numpy as np

from mnsim_noc.Communication.base_communication import BaseCommunication
from mnsim_noc.Tile.base_tile import BaseTile
from mnsim_noc.utils.component import Component
from mnsim_noc.Wire.wire_net import WireNet, _get_map_key, _get_position_key


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
    SOLVER_CONFIG = "1,1,GUROBI,norm,float"
    def __init__(self, communication_list: List[BaseCommunication], wire_net: WireNet):
        """
        init the linear programming based on the communication list and wire net
        """
        super(ScheduleLinearProgramming, self).__init__()
        # set up the params
        self.communication_list = communication_list
        self.wire_net = wire_net
        self.epsilon = 0.
        self._set_up_params(communication_list, wire_net)

    def _set_up_params(self, communication_list: List[BaseCommunication], wire_net: WireNet):
        self.logger.info("set up the params for the linear programming...")
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
        assert (np.matmul(B.T, np.ones(shape=(M, 1))) == np.zeros(shape=(K, 1))).all(), \
            "the sum of supply and demand is not zero"
        # third, get other parameters and equivalent path
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
        self.C, self.V = Cost, Value
        self.EP = EP
        self.A, self.B = A, B
        self.M, self.E, self.K, self.E_extra = M, E, K, E_extra
        # save the mapping_dice, node_index_dict and edge_index_dict
        self.mapping_dict = this_mapping_dict
        self.node_index_dict = node_index_dict
        self.edge_index_dict = edge_index_dict
        self.logger.info("set up the params for the linear programming successfully")

    def _parse_solver_config(self, solver_config):
        """
        solver config is str, in format of "1,1,GUROBI,norm,integer"
        the first two are the value of alpha and beta
        the third is type of the solver
        the fourth denote the type of the objective target, norm or max
        the fifth denote the type of the variable, integer or continuous
        """
        solver_config = solver_config.split(",")
        assert len(solver_config) == 5, \
            "the solver config must be in format of '1,1,GUROBI,norm,integer'"
        self.alpha, self.beta = float(solver_config[0]), float(solver_config[1])
        self.solver = solver_config[2]
        assert solver_config[3] in ["norm", "max"], \
            "the objective target must be norm or max"
        self.objective_target = solver_config[3]
        assert solver_config[4] in ["integer", "float"], \
            "the variable type must be integer or float"
        self.variable_type = solver_config[4]
        self.logger.info("parse the solver config successfully")
        self.logger.info(
            f"alpha: {self.alpha}, beta: {self.beta}, solver: {self.solver}, " + \
            f"objective_target: {self.objective_target}, variable_type: {self.variable_type}"
        )

    def solve(self):
        """
        solve the linear programming
        """
        # parse the solver config
        self._parse_solver_config(self.SOLVER_CONFIG)
        # define the variables
        self.logger.info("start solving the linear programming...")
        if self.variable_type == "integer":
            X = cp.Variable(shape=(self.E, self.K), integer=True)
        else:
            X = cp.Variable(shape=(self.E, self.K))
        # define two obj and constraints
        obj1 = cp.matmul(self.C.T, cp.matmul(X, self.V))
        obj2 = cp.matmul(self.EP, cp.matmul(X, self.V))
        if self.objective_target == "norm":
            obj_total = self.alpha * obj1 + self.beta * cp.norm2(obj2)
        else:
            obj_total = self.alpha * obj1 + self.beta * cp.max(obj2)
        constraints = [self.A @ X == self.B, X >= 0]
        # define and solve the problem
        Problem = cp.Problem(cp.Minimize(obj_total), constraints)
        Problem.solve(solver=self.solver, verbose=True)
        # check the status
        assert Problem.status == cp.OPTIMAL, \
            "the linear programming is not solved successfully"
        # get the result and saved into the self members
        self.optimal_x = X.value
        self.optimal_obj_total_transfer_cost = obj1.value[0][0]
        self.optimal_obj_single_wire = obj2.value[:,0]
        self.optimal_obj_in_total = Problem.value
        self.logger.info(f"the optimal total transfer cost is: {self.optimal_obj_total_transfer_cost}")
        self.logger.info(f"the optimal single wire is: {self.optimal_obj_single_wire}")
        self.logger.info("the optimal objective value is: ", self.optimal_obj_in_total)
        return self.optimal_x

    def parse_x(self, X):
        """
        parse the X matrix to the communication schedule info for each communication
        the order is the same as the input communication list
        X is in shape (E, K)
        """
        # get my X and the epsilon
        self.epsilon = np.min(np.max(self.B, axis=0)) * 1e-2
        MyX = copy.deepcopy(X)
        # check for the input X
        assert np.min(MyX) > - self.epsilon, \
            "the input X is not correct, must all be non-negative"
        assert ((np.matmul(self.A, MyX) - self.B) < self.epsilon).all(), \
            "the input X is not correct, A@X == B"
        # use A to get the node-edge link, prepared for the following process
        node_edge_relation = np.where(self.A == 1)
        node_edge_link = [[] for _ in range(self.M)]
        for node_index, edge_index in zip(node_edge_relation[0], node_edge_relation[1]):
            node_edge_link[node_index].append(edge_index)
        _get_edge_index_based_node = lambda node: node_edge_link[self.node_index_dict[node]]
        # use edge_index_dict to reverse the edge_index
        edge_index_reverse = [-1] * self.E
        for edge_description, edge_index in self.edge_index_dict.items():
            edge_index_reverse[edge_index] = edge_description
        # get the communication schedule info from MyX
        communication_schedule_info_list = [[] for _ in range(self.K)]
        for k, comm in enumerate(self.communication_list):
            # get the input tile and the end tile
            input_tile: BaseTile = comm.input_tile
            output_tile: BaseTile = comm.output_tile
            # get the start node and end node
            start_node = _get_position_key(input_tile.position)
            end_node = _get_position_key(output_tile.position)
            # get the total amount of data need to transfer
            all_transfer_data_amount = self.B[self.node_index_dict[start_node], k]
            while True:
                # check for if the outputs from the start node
                start_link_edge = _get_edge_index_based_node(start_node)
                start_link_flow = MyX[start_link_edge, k]
                if np.max(start_link_flow) < self.epsilon:
                    # there are no value need to output (small than epsilon)
                    break
                path_cost = []
                # otherwise, there must be one path to the end node
                current_node = start_node
                while True:
                    # check for if the current node is the end node
                    if current_node == end_node:
                        break
                    # otherwise
                    current_link_edge = _get_edge_index_based_node(current_node)
                    current_link_flow = MyX[current_link_edge, k]
                    # parse max edge
                    max_edge_index = current_link_edge[np.argmax(current_link_flow)]
                    max_edge_desc = edge_index_reverse[max_edge_index]
                    # get the next node
                    current_node = max_edge_desc.split("->")[1]
                    # get the cost of this path
                    cost = MyX[max_edge_index, k]
                    path_cost.append((current_node, cost))
                # get the path, check if there are loop in the path
                path = [start_node] + [x[0] for x in path_cost]
                assert len(set(path)) == len(path), \
                    "there are loop in the path"
                # get the cost of this path
                max_cost = min([x[1] for x in path_cost])
                assert max_cost > 0, \
                    "the max cost of the path small than epsilon"
                # update the MyX
                for i in range(len(path)-1):
                    edge_desc = path[i] + "->" + path[i+1]
                    edge_index = self.edge_index_dict[edge_desc]
                    MyX[edge_index, k] -= max_cost
                # add to the communication schedule info
                communication_schedule_info_list[k].append((
                    [self.mapping_dict[v] for v in path], max_cost
                ))
                all_transfer_data_amount -= max_cost
            # check for if the communication is finished
            assert all([abs(x) < self.epsilon for x in MyX[:, k]]), \
                "the communication is not finished, some value is not 0"
            # 4 for there are 4 edges at most
            assert -4 * self.epsilon < all_transfer_data_amount < 4 * self.epsilon, \
                "the communication is not finished, the all_transfer_data_amount is not 0"
        return communication_schedule_info_list
