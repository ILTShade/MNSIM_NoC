#-*-coding:utf-8-*-
"""
@FileName:
    test_wire_net.py
@Description:
    test wire net class
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2023/05/04 16:14
"""
import pytest
from mnsim_noc.Wire import WireNet

def _output_info(start_p, end_p, wn : WireNet, cate):
    transfer_path = wn.find_data_path_cate(start_p, end_p, cate)
    if transfer_path is None:
        transfer_path_flag = False
    else:
        transfer_path_flag = not wn.get_data_path_state(transfer_path)
    print("*" * 20)
    print(
        f"from start position: {start_p}" + \
        f" to end position: {end_p}"
    )
    print(
        f"state is {transfer_path_flag}," + \
        f" transfer path is {transfer_path}"
    )

def test_xy_routing():
    """
    test xy routing
    """
    wire_net = WireNet((5, 5), 1, "mesh")
    start_position = (2, 2)
    end_position_list = [
        (0, 0), (0, 2), (0, 4),
        (2, 0),         (2, 4),
        (4, 0), (4, 2), (4, 4)
    ]
    for end_position in end_position_list:
        _output_info(start_position, end_position, wire_net, "naive")

@pytest.mark.parametrize("noc_topology", ["mesh", "torus"])
@pytest.mark.parametrize("path_generator", ["naive", "adaptive", "dijkstra"])
def test_topology_path_generator(noc_topology, path_generator):
    """
    test topology and path generator
    """
    wire_net = WireNet((3, 3), 1, noc_topology)
    start_position = (0, 2)
    end_position = (1, 0)
    # base case
    print("-" * 20 + "base case" + "-" * 20)
    _output_info(start_position, end_position, wire_net, path_generator)
    # case 1
    print("-" * 20 + "case 1" + "-" * 20)
    occupy_path_list = [
        [(0, 1), (1, 1)],
        [(1, 0), (1, 1)],
        [(1, 1), (1, 2)],
        [(1, 1), (2, 1)]
    ]
    for occupy_path in occupy_path_list:
        wire_net.set_data_path_state(occupy_path, True, "0->1", 0.)
    _output_info(start_position, end_position, wire_net, path_generator)
    # case 2
    print("-" * 20 + "case 2" + "-" * 20)
    wire_net.set_data_path_state([(0, 0), (0, 1)], True, "0->1", 0.)
    _output_info(start_position, end_position, wire_net, path_generator)
    # case 3
    print("-" * 20 + "case 3" + "-" * 20)
    wire_net.set_data_path_state([(2, 0), (2, 1)], True, "0->1", 0.)
    _output_info(start_position, end_position, wire_net, path_generator)

@pytest.mark.parametrize("cate",
    ["naive", "west_first", "north_last", "negative_first", "adaptive", "dijkstra"]
)
def test_turn_model(cate):
    """
    test turn model under different cate
    """
    # init wire net
    wire_net = WireNet((5, 5), 1, "mesh")
    start_position = (2, 2)
    end_position_list = [(0, 0), (0, 4), (4, 0), (4, 4)]
    # base info
    print("-" * 20 + "base case" + "-" * 20)
    for end_position in end_position_list:
        _output_info(start_position, end_position, wire_net, cate)
    # case 1 info
    wire_net.set_data_path_state([(2, 0), (2, 1)], True, "0->1", 0.)
    wire_net.set_data_path_state([(2, 3), (2, 4)], True, "0->1", 0.)
    wire_net.set_data_path_state([(0, 2), (1, 2)], True, "0->1", 0.)
    wire_net.set_data_path_state([(3, 2), (4, 2)], True, "0->1", 0.)
    print("-" * 20 + "case 1" + "-" * 20)
    for end_position in end_position_list:
        _output_info(start_position, end_position, wire_net, cate)
    # case 2 info
    wire_net.set_data_path_state([(2, 1), (2, 2)], True, "0->1", 0.)
    wire_net.set_data_path_state([(1, 3), (2, 3)], True, "0->1", 0.)
    print("-" * 20 + "case 2" + "-" * 20)
    for end_position in end_position_list:
        _output_info(start_position, end_position, wire_net, cate)
    pass

@pytest.mark.parametrize("cate", ["adaptive", "greedy", "dijkstra", "astar"])
def test_bfs_model(cate):
    """
    test dfs model under different cate
    """
    wire_net = WireNet((5, 5), 1, "mesh")
    start_position = (4, 0)
    end_position = (0, 4)
    print("-" * 20 + "base case" + "-" * 20)
    _output_info(start_position, end_position, wire_net, cate)
    # case 1
    print("-" * 20 + "case 1" + "-" * 20)
    wire_net.set_data_path_state([(4, 2), (4, 3)], True, "0->1", 0.)
    _output_info(start_position, end_position, wire_net, cate)
    # case 2
    print("-" * 20 + "case 2" + "-" * 20)
    wire_net.set_data_path_state([(1, 1), (2, 1)], True, "0->1", 0.)
    wire_net.set_data_path_state([(1, 2), (2, 2)], True, "0->1", 0.)
    wire_net.set_data_path_state([(1, 3), (2, 3)], True, "0->1", 0.)
    wire_net.set_data_path_state([(1, 2), (1, 3)], True, "0->1", 0.)
    wire_net.set_data_path_state([(2, 2), (2, 3)], True, "0->1", 0.)
    wire_net.set_data_path_state([(3, 2), (3, 3)], True, "0->1", 0.)
    _output_info(start_position, end_position, wire_net, cate)
    pass