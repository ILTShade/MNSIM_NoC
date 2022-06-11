#-*-coding:utf-8-*-
"""
@FileName:
    test_heuristic_candidate.py
@Description:
    test heuristic candidate
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/06/11 18:42
"""
import numpy as np
from mnsim_noc.Strategy.heuristic_algorithm import Candidate

def test_candidate():
    """
    test candidate
    """
    # init parameter
    tile_row = 3
    tile_column = 3
    task_tile_num = 5
    adjacency_matrix = np.array([
        [0, 2, 4, 0, 0],
        [2, 0, 1, 3, 0],
        [4, 1, 0, 4, 0],
        [0, 3, 4, 0, 2],
        [0, 0, 0, 2, 0]
    ])
    # init candidate
    candidate_a = Candidate(tile_row, tile_column, task_tile_num, adjacency_matrix)
    candidate_b = Candidate(tile_row, tile_column, task_tile_num, adjacency_matrix)
    # mutation candidate
    candidate_c = candidate_a.mutation()
    candidate_d = candidate_b.mutation()
    # crossover candidate
    candidate_e = Candidate.crossover(candidate_c, candidate_d)
