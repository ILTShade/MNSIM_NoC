#-*-coding:utf-8-*-
"""
@FileName:
    mapping.py
@Description:
    mapping strategy for behavior driven simulation
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 20:43
"""
import abc
import random
import copy
import numpy as np
import time
import pickle
import os
from mnsim_noc.Buffer.base_buffer import get_data_size
from mnsim_noc.utils.component import Component
from mnsim_noc.Tile import BaseTile
from mnsim_noc.Wire import WireNet
# from mnsim_noc.Wire.wire_net import _get_map_key
from mnsim_noc.Communication import BaseCommunication
from mnsim_noc.Strategy.heuristic_algorithm import Candidate
# import torch
# from torch_geometric.data import Data
# from torch_geometric.nn import GCNConv
# import torch.nn.functional as F
# import math

class Mapping(Component):
    """
    mapping strategy for behavior driven simulation
    """
    REGISTRY = "mapping"
    def __init__(self, task_behavior_list, image_num,
        tile_net_shape, buffer_size, band_width
    ):
        super(Mapping, self).__init__()
        self.task_behavior_list = task_behavior_list
        self.image_num = image_num
        self.tile_row = tile_net_shape[0]
        self.tile_column = tile_net_shape[1]
        self.buffer_size = buffer_size
        self.band_width = band_width

    def get_adjacency_matrix(self, tile_behavior_list):
        """
        get adjacency matrix
        """
        # get and set the adjacency matrix
        task_tile_num = len(tile_behavior_list)
        adjacency_matrix = np.zeros(
            shape=(task_tile_num, task_tile_num),
            dtype=np.int64
        )
        for i in range(task_tile_num):
            for j in range(task_tile_num):
                if i == j:
                    continue
                # task id must be the same
                if tile_behavior_list[i]["task_id"] != tile_behavior_list[j]["task_id"]:
                    continue
                # j in the target tile id
                if tile_behavior_list[j]["tile_id"] not in \
                    tile_behavior_list[i]["target_tile_id"]:
                    continue
                # calculate the communication amount
                transfer_amount = sum([
                    get_data_size(v["output"][0])
                    for v in tile_behavior_list[i]["dependence"]
                ])
                adjacency_matrix[i][j] = transfer_amount
                adjacency_matrix[j][i] = transfer_amount
        return task_tile_num, adjacency_matrix

    @abc.abstractmethod
    def _get_position_list(self, tile_behavior_list):
        """
        get position in list shape
        """
        raise NotImplementedError

    def _check_position_list(self, position_list, tile_behavior_list):
        """
        check position list
        the length of position list should be equal to the length of tile_list
        all position should be tuple and inside the range of tile_net_shape
        """
        assert len(position_list) == len(tile_behavior_list), \
            "the length of position list should be equal to the length of tile_list"
        for position in position_list:
            assert isinstance(position, tuple), \
                "all position should be tuple"
            assert len(position) == 2, \
                "all position should be tuple with length 2"
            assert 0 <= position[0] < self.tile_row and 0 <= position[1] < self.tile_column, \
                "all position should be inside the range of tile_net_shape"

    def mapping_net(self):
        """
        mapping net
        """
        tile_behavior_list = []
        for task_id, task_behavior in enumerate(self.task_behavior_list):
            # modify the tile task id
            for tile_behavior in task_behavior:
                tile_behavior["task_id"] = task_id
                tile_behavior_list.append(tile_behavior)
        # get position, output pair list, fitness and position list
        output_pair_list = self._get_position_list(tile_behavior_list)
        output_behavior_list = []
        for output_pair in output_pair_list:
            fitness, position_list = output_pair
            self._check_position_list(position_list, tile_behavior_list)
            # get tile list
            tile_list = []
            for position, tile_behavior in zip(position_list, tile_behavior_list):
                tile = BaseTile(position, self.image_num, self.buffer_size, tile_behavior)
                tile_list.append(tile)
            # get wire net
            wire_net = WireNet((self.tile_row, self.tile_column), self.band_width)
            # communication list
            communication_list = []
            for start_tile in tile_list:
                end_tile_task_id = start_tile.task_id
                end_target_tile_id_list = start_tile.target_tile_id
                for end_tile in tile_list:
                    if end_tile.task_id == end_tile_task_id \
                        and end_tile.tile_id in end_target_tile_id_list:
                        communication = BaseCommunication(start_tile, end_tile, wire_net)
                        communication_list.append(communication)
            output_behavior_list.append((
                fitness, tile_list, communication_list, wire_net
            ))
        # return tile_list, communication_list, wire_net
        return output_behavior_list

    def get_update_order(self, tile_list, communication_list):
        """
        get update order, first write the read
        """
        update_module = []
        communication_in_ids = []
        for tile in tile_list:
            # first, communication output tile is this tile
            for communication in communication_list:
                if communication.output_tile is tile and \
                    id(communication) not in communication_in_ids:
                    communication_in_ids.append(id(communication))
                    update_module.append(communication)
            # this tile
            update_module.append(tile)
            # last for the communication input tile is this tile
            for communication in communication_list:
                if communication.input_tile is tile and \
                    id(communication) not in communication_in_ids:
                    communication_in_ids.append(id(communication))
                    update_module.append(communication)
        return update_module

class NaiveMapping(Mapping):
    """
    naive mapping
    """
    NAME = "naive"
    def _get_position_list(self, tile_behavior_list):
        """
        get position list
        """
        position_list = []
        for i in range(len(tile_behavior_list)):
            # get position
            position_row = i // self.tile_column
            position_column = i % self.tile_column
            position_list.append((position_row, position_column))
        return [(None, position_list)]

class SnakeMapping(Mapping):
    """
    snake mapping
    """
    NAME = "snake"
    def _get_position_list(self, tile_behavior_list):
        """
        get position list
        0, 1, 8,
        3, 2, 7,
        4, 5, 6,
        """
        position_list = []
        for i in range(min(self.tile_row, self.tile_column)):
            # get position
            row = [(i, j) for j in range(0, i)]
            point = [(i, i)]
            column = [(j, i) for j in range(i-1, -1, -1)]
            line = row + point + column
            line = line[::-1] if i % 2 == 1 else line
            # add to position list
            position_list += line
        # return list
        return [(None, position_list[:len(tile_behavior_list)])]

class PresetMapping(Mapping):
    """
    preset mapping
    """
    NAME = "preset"
    def _get_position_list(self, tile_behavior_list):
        with open("/home/nfs_data/sunhanbo/heuristic_mapping/position_list.pkl", "rb") as f:
            position_list = pickle.load(f)
        assert len(position_list) == len(tile_behavior_list), \
            "the length of position list should be equal to the length of tile_list"
        return [(None, position_list)]

# class MyGCN(torch.nn.Module):
#     """
#     my gcn model
#     """
#     def __init__(self):
#         """
#         init conv layers
#         """
#         super(MyGCN, self).__init__()
#         self.conv1_1 = GCNConv(6, 16)
#         self.conv1_2 = GCNConv(16, 16)
#         self.conv2_1 = GCNConv(16, 16)
#         self.conv2_2 = GCNConv(16, 2)
#     def forward(self, data):
#         """
#         forward
#         """
#         x, edge_index = data.x, data.edge_index
#         # forward
#         x = F.relu(self.conv1_1(x, edge_index))
#         x = F.relu(self.conv1_2(x, edge_index))
#         # dropout
#         x = F.dropout(x, p=0.5, training=self.training)
#         # for the second stage
#         x = F.relu(self.conv2_1(x, edge_index))
#         x = self.conv2_2(x, edge_index)
#         return x

# class for individuals and its behavior
class Individual:
    """
    individual class for genetic algorithm
    """
    scale = 0.1
    def __init__(self, tile_row, tile_column, tile_num, rank_list, adjacency_matrix):
        self.tile_row = tile_row
        self.tile_column = tile_column
        self.tile_num = tile_num
        self.total_comm = 0
        self.rank_list = rank_list
        self.adjacency_matrix = adjacency_matrix
        self.map_list = [[-1]*self.tile_column for _ in range(0,self.tile_row)]
        self.position_list = [None]*tile_num

    # tool functions for mapping
    def get_nearest_pos(self, pos, map_list):
        """
        get nearest position
        """
        for distance in range(1,self.tile_row+self.tile_column-1):
            for loc in [(i+pos[0],distance-abs(i)+pos[1]) for i in range(-distance,distance)]+[(i+pos[0],abs(i)-distance+pos[1]) for i in range(distance,-distance,-1)]:
                if 0<=loc[0]<self.tile_row and 0<=loc[1]<self.tile_column and map_list[loc[0]][loc[1]] == -1:
                    return loc

    def get_random_point(self, position_list):
        """
        get a random point
        """
        loc_list = []
        for row in range(0,self.tile_row):
            for column in range(0,self.tile_column):
                pos_tmp = (row,column)
                # already mapped
                if pos_tmp in position_list:
                    continue
                loc_list.append(pos_tmp)
        # random choose
        loc = loc_list[random.randint(0,len(loc_list)-1)]
        return loc
    # random initialize
    def random_mapping(self):
        """
        random mapping
        """
        for link in self.rank_list:
            tile_1 = link[0][0]
            tile_2 = link[0][1]
            pos_1 = self.position_list[tile_1]
            pos_2 = self.position_list[tile_2]
            if pos_1:
                if pos_2:
                    continue
                else:
                    loc = self.get_nearest_pos(pos_1, self.map_list)
                    self.position_list[tile_2] = loc
                    self.map_list[loc[0]][loc[1]] = tile_2
            else:
                if pos_2:
                    loc = self.get_nearest_pos(pos_2, self.map_list)
                    self.position_list[tile_1] = loc
                    self.map_list[loc[0]][loc[1]] = tile_1
                else:
                    # map the first tile on the best point
                    loc_1 = self.get_random_point(self.position_list)
                    self.position_list[tile_1] = loc_1
                    self.map_list[loc_1[0]][loc_1[1]] = tile_1
                    # map the second tile on the nearest place
                    loc_2 = self.get_nearest_pos(loc_1, self.map_list)
                    self.position_list[tile_2] = loc_2
                    self.map_list[loc_2[0]][loc_2[1]] = tile_2
    # mutation
    def mutation_exchange(self, parent):
        """
        mutation exchange
        """
        pass
    def mutation_reverse(self, parent):
        """
        mutation reverse
        """
        pass
    def mutation_insert(self, parent):
        """
        mutation insert
        """
        pass
    def mutation_remap(self, parent):
        """
        mutation remap
        """
        self.map_list = copy.deepcopy(parent.map_list)
        self.position_list = copy.deepcopy(parent.position_list)
        cut_place = random.randint(0,self.tile_num-1)
        for tile_id in range(cut_place,self.tile_num):
            loc = self.position_list[tile_id]
            self.map_list[loc[0]][loc[1]] = -1
            self.position_list[tile_id] = None
        self.random_mapping()
    # crossover
    def crossover(self, parent1, parent2):
        """
        crossover
        """
        pass
    # update total comm
    def s_update_total_comm(self):
        """
        update total comm
        """
        total_comm = 0
        for link in self.rank_list:
            tile_1 = link[0][0]
            tile_2 = link[0][1]
            pos_1 = self.position_list[tile_1]
            pos_2 = self.position_list[tile_2]
            comm = link[1]
            total_comm += comm * (abs(pos_1[0]-pos_2[0])+abs(pos_1[1]-pos_2[1]))
        self.total_comm = total_comm

#     def update_total_comm(self, model):
#         """
#         update total comm based on GNN
#         """
#         communication_info_list = []
#         communication_path_list = []
#         for i in range(self.tile_num):
#             for j in range(self.tile_num):
#                 if j <= i:
#                     continue # pass
#                 amount = self.adjacency_matrix[i][j]
#                 if amount <= 0:
#                     continue
#                 position_start = self.position_list[i]
#                 position_end = self.position_list[j]
#                 length = abs(position_start[0]-position_end[0])+abs(position_start[1]-position_end[1])
#                 # position embedding
#                 position_start_x = math.sin(position_start[0]*2*math.pi/16)
#                 position_start_y = math.sin(position_start[1]*2*math.pi/16)
#                 position_end_x = math.sin(position_end[0]*2*math.pi/16)
#                 position_end_y = math.sin(position_end[1]*2*math.pi/16)
#                 communication_info_list.append(
#                     [amount, length, position_start_x, position_start_y, position_end_x, position_end_y]
#                 )
#                 communication_path_list.append(get_path(position_start, position_end))
#         x = torch.from_numpy(np.array(communication_info_list)).to(dtype=torch.float)
#         base_total = torch.sum(x[:,0] * x[:,1]).item() / 8 / 4e5
#         x = torch.div(x, torch.FloatTensor([1.2e6, 1.2e1, 1, 1, 1, 1]))
#         # get edge
#         L = len(communication_path_list)
#         assert L == 101
#         bool_matrix = [[0]*L for i in range(L)]
#         for i in range(L):
#             for j in range(L):
#                 if i == j:
#                     continue
#                 if len(set(communication_path_list[i]) & set(communication_path_list[j])) == 0:
#                     bool_matrix[i][j] = 0
#                 else:
#                     bool_matrix[i][j] = 1
#         edge_index = np.array(bool_matrix)
#         edge_index = torch.from_numpy(np.stack(np.nonzero(edge_index))).to(torch.long)
#         # forward
#         data = Data(x=x, edge_index=edge_index)
#         model.eval()
#         with torch.no_grad():
#             output = model(data)
#             output = torch.max(2*output[:,0]+output[:,1], 0, keepdim=True)[0]
#         self.total_comm = output.item() + Individual.scale * base_total

# def get_path(start_position, end_position):
#     """
#     get path
#     """
#     current_position = [start_position[0], start_position[1]]
#     path = []
#     while True:
#         path.append(tuple(current_position))
#         # first left or right
#         if current_position[1] != end_position[1]:
#             current_position[1] += 1 if current_position[1] < end_position[1] else -1
#         elif current_position[0] != end_position[0]:
#             current_position[0] += 1 if current_position[0] < end_position[0] else -1
#         else:
#             break
#     naive_path = [_get_map_key((path[i], path[i+1])) for i in range(len(path)-1)] # get wire
#     return naive_path

class NSGA_II(Mapping):
    """
    NSGA_II Mapping algorithm
    """
    NAME = "nsga2_optimal"
    def _get_position_list(self, tile_behavior_list):
        # init gcn
        # model = MyGCN()
        # model.load_state_dict(torch.load("./vgg8_gnn_params.pth"))
        # model.eval()
        # rank the transferred data amount between tiles
        data_dict = dict()
        data_matrix = [[0]*len(tile_behavior_list) for _ in range(0,len(tile_behavior_list))]
        for tile_behavior in tile_behavior_list:
            tile_id = tile_behavior["tile_id"]
            target_tile_list = tile_behavior["target_tile_id"]
            transfer_list = tile_behavior["dependence"]
            transfer_amount = 0
            for data in transfer_list:
                outputs = data["output"]
                for output in outputs:
                    transfer_amount += (output[3] - output[2]) * output[4]
            for target_tile_id in target_tile_list:
                if target_tile_id >= 0:
                    data_dict[(tile_id,target_tile_id)] = transfer_amount
                    data_matrix[tile_id][target_tile_id] = transfer_amount
        # adjacency matrix
        # _, adjacency_matrix = self.get_adjacency_matrix(tile_behavior_list)
        # info for mapping
        rank_list = sorted(data_dict.items(),key=lambda s:s[1],reverse=True)    #[((tile_id,target_tile_id),transfer_amount)]
        tile_num = len(tile_behavior_list)
        # 0.parameters
        N = 200
        maxGEN = 300
        save_position_list = []
        time_cost_list = []
        # crossover_probability = 1.0
        mutation_probability = 1.0
        # 1.random initialize
        population = []
        for i in range(0,N):
            individual = Individual(self.tile_row,self.tile_column,tile_num,rank_list,None)
            individual.random_mapping()
            # individual.update_total_comm(model)
            individual.s_update_total_comm()
            population.append(individual)
        # 2.first generation child
        # 2.1 tournament
        # 2.2 crossover/mutation
        # 3.repeated evolution
        for round in range(0,maxGEN):
            self.logger.info(f"round: {round}")
            child=[]
            start_time = time.time()
            for individual in population:
                # if mutation happens
                if random.random() < mutation_probability:
                    new_child = Individual(self.tile_row,self.tile_column,tile_num,rank_list,None)
                    new_child.mutation_remap(individual)
                    # new_child.update_total_comm(model)
                    individual.s_update_total_comm()
                    child.append(new_child)
            # for last
            if round == maxGEN-1:
                for individual in population+child:
                    # individual.update_total_comm(model)
                    pass
            select = sorted(population+child,key=lambda s:s.total_comm)
            population = select[:N]
            end_time = time.time()
            save_position_list.append([
                copy.deepcopy(x.position_list) for x in population
            ])
            time_cost_list.append(end_time-start_time)
            # print('min comm:'+str(population[0].total_comm))
        # 3.1 tournament
        # 3.2 crossover/mutation
        # 3.3 select choice
        # 4 choose the best mapping result
        position_list = population[0].position_list
        while True:
            file_name = f"{self.NAME}_position_time_record_{random.randint(1, 99):02d}.pkl"
            if os.path.exists(file_name):
                continue
            with open(file_name, "wb") as f:
                pickle.dump(save_position_list, f)
                pickle.dump(time_cost_list, f)
            break
        self.logger.info(f"save file to {file_name}")
        # return list
        return [(None, position_list)]

class HeuristicMapping(Mapping):
    """
    heuristic mapping based on heuristic candidate
    """

    NAME = "heuristic_baseline"
    def _get_position_list(self, tile_behavior_list):
        """
        get position list as heuristic baseline
        """
        # get task tile number and adjacency matrix
        task_tile_num, adjacency_matrix = self.get_adjacency_matrix(tile_behavior_list)
        # heuristic search, init parameters
        N = 200
        max_generation = 300
        # 1, init the population, with N possible candidate
        population = [
            Candidate(self.tile_row, self.tile_column, task_tile_num, adjacency_matrix)
            for _ in range(N)
        ]
        save_position_list = []
        time_cost_list = []
        output_position_list = []
        # 2, mutation, crossover, and filter, for max_generation epoch
        for _ in range(max_generation):
            start_time = time.time()
            # 2.1, mutation for all
            mutation_population = [candidate.mutation() for candidate in population]
            # 2.2, crossover, based on the fitness ad the probability
            probability = np.array([1./candidate.fitness for candidate in population])
            probability = probability / probability.sum()
            crossover_pair = np.random.choice(
                list(range(len(population))),
                size=(len(population), 2),
                p=probability
            ).tolist()
            crossover_population = [
                Candidate.crossover(population[pair[0]], population[pair[1]])
                for pair in crossover_pair
            ]
            # 2.3, filter the population
            population = population + mutation_population + crossover_population
            population = sorted(
                population,
                key=lambda candidate: candidate.fitness
            )
            population = population[:N]
            end_time = time.time()
            save_position_list.append([
                copy.deepcopy(x.position_list) for x in population
            ])
            time_cost_list.append(end_time-start_time)
            # log info
            # self.logger.info(f"Iteration {_}, the best amount is {population[0].fitness}")
            choice_index = 0
            output_position_list.append((
                population[choice_index].fitness,
                population[choice_index].position_list,
            ))
        # save for file
        while True:
            file_name = f"{self.NAME}_position_time_record_{random.randint(1, 99):02d}.pkl"
            if os.path.exists(file_name):
                continue
            with open(file_name, "wb") as f:
                pickle.dump(save_position_list, f)
                pickle.dump(time_cost_list, f)
            break
        self.logger.info(f"save file to {file_name}")
        # output the best candidate
        # return population[0].position_list
        return [output_position_list[-1]]
