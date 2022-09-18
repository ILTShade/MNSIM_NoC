#-*-coding:utf-8-*-
"""
@FileName:
    heuristic_algorithm.py
@Description:
    heuristic algorithm for mapping
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/06/07 16:08
"""
import math
import copy
import numpy as np
from mnsim_noc.utils.component import Component

class Individual(Component):
    """
    individual class for heuristic node grouping
    """
    REGISTRY = "individual"
    NAME = "node_grouping"

    def __init__(self, tile_row, tile_column, tile_num, rank_list):
        """
        init for individual, rank_list is a ordered list
        [((start_tile_id, end_tile_id), comm)]
        The most important params are map_list and position_list
        """
        super(Individual).__init__()
        self.tile_row = tile_row
        self.tile_column = tile_column
        self.tile_num = tile_num
        self.total_comm = 0
        self.rank_list = rank_list
        self.map_list = [[-1]*self.tile_column for _ in range(0,self.tile_row)]
        self.position_list = [None]*tile_num
        self.hash_label = None

    # tool functions for random mapping
    def get_nearest_pos(self, pos, map_list):
        """
        get nearest position, random if there are multiple
        """
        max_distance = self.tile_row - 1 + self.tile_column - 1
        for distance in range(1, max_distance + 1):
            pl1 = [
                (pos[0] + i, pos[1] + distance - abs(i))
                for i in range(-distance, distance)
            ]
            pl2 = [
                (pos[0] + i, pos[1] - distance + abs(i))
                for i in range(distance, -distance, -1)
            ]
            pl = list(set(pl1) | set(pl2))
            assert len(pl) == distance * 4
            pl = list(filter(
                lambda loc: 0 <= loc[0] < self.tile_row and \
                    0 <= loc[1] < self.tile_column and \
                    map_list[loc[0]][loc[1]] == -1,
                pl
            ))
            # if there is no pl, continue
            if len(pl) == 0:
                continue
            choice_index = np.random.choice(len(pl), 1)[0]
            return pl[choice_index]

    def get_random_point(self, tile_id, map_list, position_list):
        """
        get a random point
        for specified tile id, random probability to get a random point
        """
        # get position dict probability
        position_dict = {}
        for i in range(self.tile_row):
            for j in range(self.tile_column):
                status = map_list[i][j]
                if status == -1:
                    # there is no tile here
                    continue
                for offset_x, offset_y in [(0,1),(-1,0),(0,-1),(1,0)]:
                    x = i + offset_x
                    y = j + offset_y
                    if 0 <= x < self.tile_row and \
                        0 <= y < self.tile_column and \
                        map_list[x][y] == -1:
                        # get probability to get a random point
                        if (x,y) not in position_dict.keys():
                            position_dict[(x,y)] = abs(tile_id - map_list[i][j])
                        else:
                            position_dict[(x,y)] = min(
                                position_dict[(x,y)],
                                abs(tile_id - map_list[i][j])
                            )
        # get a random point
        position_list = list(position_dict.items())
        if len(position_list) == 0:
            return (int(self.tile_row/2), int(self.tile_column/2))
        pl = [x[0] for x in position_list]
        pp = np.array([x[1]**(-1) for x in position_list])
        pp = pp/np.sum(pp)
        choice_index = np.random.choice(len(pl), 1, p=pp)[0]
        return pl[choice_index]

    # generate a random mapping result
    def random_mapping(self):
        """
        random mapping based on the rank list
        """
        for link in self.rank_list:
            tile_1 = link[0][0]
            tile_2 = link[0][1]
            pos_1 = self.position_list[tile_1]
            pos_2 = self.position_list[tile_2]
            if pos_1 is not None:
                if pos_2 is not None:
                    continue
                loc = self.get_nearest_pos(pos_1, self.map_list)
                self.position_list[tile_2] = loc
                self.map_list[loc[0]][loc[1]] = tile_2
            else:
                if pos_2 is not None:
                    loc = self.get_nearest_pos(pos_2, self.map_list)
                    self.position_list[tile_1] = loc
                    self.map_list[loc[0]][loc[1]] = tile_1
                else:
                    # the most important part
                    loc_1 = self.get_random_point(tile_1, self.map_list, self.position_list)
                    self.position_list[tile_1] = loc_1
                    self.map_list[loc_1[0]][loc_1[1]] = tile_1
                    # map the second tile on the nearest place
                    loc_2 = self.get_nearest_pos(loc_1, self.map_list)
                    self.position_list[tile_2] = loc_2
                    self.map_list[loc_2[0]][loc_2[1]] = tile_2

    # mutation for the parent
    def mutation_remap(self, parent):
        """
        mutation for one parent individual
        """
        self.map_list = copy.deepcopy(parent.map_list)
        self.position_list = copy.deepcopy(parent.position_list)
        # mutate scale of total position, not only last part
        ratio = 0.16667
        cut_index = np.random.choice(a=self.tile_num, size=int(self.tile_num*ratio), replace=False)
        cut_index = cut_index.tolist()
        for index in cut_index:
            loc = self.position_list[index]
            # re initialize the position
            self.position_list[index] = None
            self.map_list[loc[0]][loc[1]] = -1
        self.random_mapping()

    # crossover
    def crossover(self, parent1, parent2):
        """
        crossover for two parent individual
        """
        raise NotImplementedError

    def _get_unique_hash(self, position_list):
        """
        get unique hash for the position list
        """
        hash_position_list = []
        for i in range(self.tile_num):
            assert position_list[i] is not None, \
                "position list should not be None"
            hash_position_list.append(position_list[i][0]*self.tile_column + position_list[i][1])
        return str(hash_position_list)

    # update total comm
    def update_total_comm(self):
        """
        get update total comm
        """
        total_comm = 0.
        for link in self.rank_list:
            tile_1 = link[0][0]
            tile_2 = link[0][1]
            pos_1 = self.position_list[tile_1]
            pos_2 = self.position_list[tile_2]
            comm = link[1]
            total_comm += comm * (abs(pos_1[0]-pos_2[0])+abs(pos_1[1]-pos_2[1]))
        self.total_comm = total_comm
        # update unique hash
        self.hash_label = self._get_unique_hash(self.position_list)

class Candidate(Component):
    """
    candidate class for heuristic algorithm
    """
    REGISTRY = "candidate"
    NAME = "heuristic"
    HISTORY = []
    CHECK_MAX = 3

    @classmethod
    def check_and_add_history(cls, position_list):
        """
        check if the position list is already in the history
        """
        position_list = str(position_list)
        if position_list in cls.HISTORY:
            return False
        cls.HISTORY.append(position_list)
        return True

    def __init__(
        self, tile_row, tile_column, task_tile_num, adjacency_matrix,
        hidden_vector=None, position_list=None
    ):
        """
        initialize candidate
        tile_row, tile_column, the shape of the system
        task_tile_num, the total tile number of all of the tasks
        adjacency_matrix, the adjacency matrix of the communication tile
        """
        super(Candidate, self).__init__()
        self.tile_row, self.tile_column = tile_row, tile_column
        self.task_tile_num = task_tile_num
        self.adjacency_matrix = adjacency_matrix
        # the adjacency matrix must be in shape of (task_tile_num, task_tile_num)
        assert self.adjacency_matrix.shape == (self.task_tile_num, self.task_tile_num), \
            "the shape of the adjacency matrix must be (task_tile_num, task_tile_num)"
        # hidden vector and position list both or neither be None
        assert (hidden_vector is None and position_list is None) or \
            (hidden_vector is not None and position_list is not None), \
            f"hidden vector and position list both or neither be None"
        # random init the hidden_vector, and check history
        if hidden_vector is None:
            for _ in range(self.CHECK_MAX):
                self.hidden_vector = np.random.uniform(0, 1, (self.tile_row, self.tile_column))
                self.hidden_vector = self.hidden_vector / np.linalg.norm(self.hidden_vector)
                self.position_list = self._get_position_list(self.hidden_vector)
                if Candidate.check_and_add_history(self.position_list):
                    break
        else:
            self.hidden_vector = hidden_vector
            self.position_list = position_list
        # get the fitness
        self.fitness = self._get_fitness(self.position_list)

    def _get_position_list(self, hidden_vector):
        """
        get the position list of the position
        based on the hidden vector
        """
        # get the max value index
        position_list = list(map(
            lambda x: (x // self.tile_column, x % self.tile_column),
            np.argsort(hidden_vector, axis=None)
        ))
        return position_list[-1:-1-self.task_tile_num:-1]

    def _get_fitness(self, position_list):
        """
        get the fitness of the candidate to the environment
        """
        total_count = 0.
        for i in range(self.task_tile_num):
            for j in range(i+1, self.task_tile_num):
                # based on the adjacency matrix, and the position list
                position_i, position_j = position_list[i], position_list[j]
                distance = abs(position_i[0] - position_j[0]) + \
                    abs(position_i[1] - position_j[1])
                # count
                total_count += self.adjacency_matrix[i, j] * distance
        return float(total_count)

    @classmethod
    def crossover(cls, candidate_a, candidate_b):
        """
        crossover two candidate, more fitness, less weight
        """
        # set the crossover parameter
        crossover_k = 1
        # get the probability of crossover candidate, based on candidate_a
        probability_a = 1 / (1 + (candidate_a.fitness/candidate_b.fitness)**crossover_k)
        # based on probability_a, generate random 0, 1, hard mode
        for _ in range(Candidate.CHECK_MAX):
            choices = np.random.choice([1, 0],
                size = candidate_a.hidden_vector.shape,
                p = [probability_a, 1-probability_a]
            )
            hidden_vector = choices * candidate_a.hidden_vector + \
                (1-choices) * candidate_b.hidden_vector
            hidden_vector = hidden_vector / np.linalg.norm(hidden_vector)
            position_list = candidate_a._get_position_list(hidden_vector)
            if Candidate.check_and_add_history(position_list):
                break
        # return new candidate
        return Candidate(
            candidate_a.tile_row, candidate_a.tile_column,
            candidate_a.task_tile_num, candidate_a.adjacency_matrix,
            hidden_vector, position_list
        )

    def mutation(self):
        """
        mutation the candidate
        """
        # set the mutation parameter
        mutation_k = 1. / math.sqrt(self.tile_row * self.tile_column)
        # new candidate
        for _ in range(Candidate.CHECK_MAX):
            adds = mutation_k * np.random.uniform(0, 1, (self.tile_row, self.tile_column))
            hidden_vector = self.hidden_vector + adds
            hidden_vector = hidden_vector / np.linalg.norm(hidden_vector)
            position_list = self._get_position_list(hidden_vector)
            if Candidate.check_and_add_history(position_list):
                break
        # return new candidate
        return Candidate(
            self.tile_row, self.tile_column,
            self.task_tile_num, self.adjacency_matrix,
            hidden_vector, position_list
        )
