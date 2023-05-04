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
        transfer_path = wire_net.find_data_path_cate(
            start_position, end_position, "naive"
        )
        print("*" * 20)
        print(f"start position is {start_position}, end position is {end_position}")
        print(f"transfer path is {transfer_path}")

@pytest.mark.parametrize("cate", ["naive", "west_first", "north_last", "negative_first", "adaptive", "dijkstra"])
def test_turn_model(cate):
    """
    test turn model under different cate
    """
    # init wire net
    wire_net = WireNet((5, 5), 1, "mesh")
    start_position = (2, 2)
    end_position_list = [(0, 0), (0, 4), (4, 0), (4, 4)]
    def _output_info():
        for end_position in end_position_list:
            transfer_path = wire_net.find_data_path_cate(
                start_position, end_position, cate
            )
            if transfer_path is None:
                transfer_path_flag = False
            else:
                transfer_path_flag = not wire_net.get_data_path_state(transfer_path)
            print("*" * 20)
            print(
                f"start position is {start_position}" + \
                f" end position is {end_position}"
            )
            print(
                f"state is {transfer_path_flag}," + \
                f" transfer path is {transfer_path}"
            )
    # base info
    _output_info()
    # case 1 info
    wire_net.set_data_path_state([((2, 0), (2, 1))], True, "0->1", 0.)
    wire_net.set_data_path_state([((2, 3), (2, 4))], True, "0->1", 0.)
    wire_net.set_data_path_state([((0, 2), (1, 2))], True, "0->1", 0.)
    wire_net.set_data_path_state([((3, 2), (4, 2))], True, "0->1", 0.)
    print("-" * 20 + "case 1" + "-" * 20)
    _output_info()
    # case 2 info
    wire_net.set_data_path_state([((2, 1), (2, 2))], True, "0->1", 0.)
    wire_net.set_data_path_state([((1, 3), (2, 3))], True, "0->1", 0.)
    print("-" * 20 + "case 2" + "-" * 20)
    _output_info()
