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
import time
import pickle
import os
import numpy as np
from mnsim_noc.Buffer.base_buffer import get_data_size
from mnsim_noc.utils.component import Component
from mnsim_noc.Tile import BaseTile
from mnsim_noc.Wire import WireNet
from mnsim_noc.Communication import BaseCommunication
from mnsim_noc.Strategy.heuristic_algorithm import Individual,Candidate

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

class ImpactMapping(Mapping):
    """
    impact mapping
    """
    NAME = "impact"
    def _get_position_list(self, tile_behavior_list):
        """
        get position list
        0, 1, 2,
        5, 4, 3,
        6, 7, 8,
        """
        position_list = []
        for i in range(self.tile_row):
            row = [(i, j) for j in range(self.tile_column)]
            row = row[::-1] if i % 2 == 1 else row
            position_list += row
        # return list
        return [(None, position_list[:len(tile_behavior_list)])]

class PresetMapping(Mapping):
    """
    preset mapping
    """
    NAME = "preset"
    def _get_position_list(self, tile_behavior_list):
        file_name = os.path.join(
            "/home/nfs_data/sunhanbo/heuristic_mapping/outputs",
            "node_gnn_resnet18_search_process.pkl"
        )
        with open(file_name, "rb") as f:
            position_population = pickle.load(f)
        for position_list in position_population:
            assert len(position_list) == len(tile_behavior_list), \
                "the length of position list should be equal to the length of tile_list"
        self.logger.info(f"load from {file_name}")
        return [(None, position_list) for position_list in position_population]


class NodeGroup(Mapping):
    """
    node group algorithm
    """
    NAME = "node_group"
    def _get_position_list(self, tile_behavior_list):
        # get adjacency matrix
        task_tile_num, adjacency_matrix = self.get_adjacency_matrix(tile_behavior_list)
        data_dict = {}
        for i in range(task_tile_num):
            for j in range(i+1, task_tile_num):
                if adjacency_matrix[i][j] > 0:
                    data_dict[(i,j)] = adjacency_matrix[i][j]
        # info for mapping, [((tile_id,target_tile_id),transfer_amount)]
        rank_list = sorted(list(data_dict.items()), key=lambda s:s[1], reverse=True)
        tile_num = len(tile_behavior_list)
        assert tile_num == task_tile_num
        # save for file
        save_position_list = []
        time_cost_list = []
        # 0. parameters
        N = 200
        maxGEN = 300
        population = []
        for _ in range(N):
            individual = Individual(self.tile_row, self.tile_column, tile_num, rank_list)
            individual.random_mapping()
            individual.update_total_comm()
            population.append(individual)
        # 1. generation child
        for epoch in range(maxGEN):
            self.logger.info(f"epoch: {epoch}")
            child = []
            start_time = time.time()
            for individual in population:
                new_child = Individual(self.tile_row, self.tile_column, tile_num, rank_list)
                new_child.mutation_remap(individual)
                new_child.update_total_comm()
                child.append(new_child)
            elite = sorted(population+child, key=lambda s:s.total_comm)
            population = elite[:N]
            end_time = time.time()
            save_position_list.append([
                copy.deepcopy(x.position_list) for x in population
            ])
            time_cost_list.append(end_time-start_time)
        # 3. choose the best mapping result
        position_list = population[0].position_list
        self.logger.info(f"final min comm: {population[0].total_comm}")
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
