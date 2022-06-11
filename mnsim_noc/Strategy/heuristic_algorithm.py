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
import numpy as np
from mnsim_noc.utils.component import Component

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
        return total_count

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
