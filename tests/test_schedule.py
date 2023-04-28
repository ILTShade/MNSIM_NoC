#-*-coding:utf-8-*-
"""
@FileName:
    test_schedule.py
@Description:
    test schedule step for each communication
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2023/04/28 22:29
"""
import pickle

import pytest

from mnsim_noc.Array import BaseArray
from mnsim_noc.Strategy import Schedule
from mnsim_noc.utils.yaml_io import read_yaml


@pytest.mark.parametrize("config, task", [("examples/test.yaml", "examples/test.pkl")])
def test_schedule(config, task):
    """
    test schedule step for each communication
    """
    # load array config
    array_config = read_yaml(config)
    task_name_label = "test"
    image_num = array_config.get("image_num")
    tile_net_shape = (
        array_config.get("tile_array_row"),
        array_config.get("tile_array_col")
    )
    buffer_size = (
        array_config.get("input_buffer_size"),
        array_config.get("output_buffer_size")
    )
    band_width = array_config.get("band_width")
    mapping_strategy = "naive"
    schedule_strategy = "naive"
    transparent_flag = False
    # load task
    task_behavior_list = []
    with open(task, "rb") as f:
        task_behavior_list.append(pickle.load(f))
    # create array
    array = BaseArray(
        task_name_label,
        task_behavior_list, image_num,
        tile_net_shape, buffer_size, band_width,
        mapping_strategy, schedule_strategy, transparent_flag
    )
    # init schedule
    assert len(array.output_behavior_list) == 1, \
        f"output behavior list is {array.output_behavior_list}"
    _, _, communication_list, wire_net = array.output_behavior_list[0]
    wire_net.set_transparent_flag(transparent_flag)
    schedule_strategy = Schedule.get_class_(schedule_strategy)(communication_list, wire_net)
    # base test for the schedule strategy
    # for communication in communication_list:
    #     print(communication.input_tile.position, communication.output_tile.position)
    # from the output results, we choose communication 3 as the test case
    print("\n"+"*"*20+"test case"+"*"*20)
    communication_id = 3
    path_flag, transfer_path = schedule_strategy._find_check_path(communication_id)
    print(f"base case: {path_flag}, {transfer_path}")
    # test case 1
    occupy_path = [((1,1),(0,1)), ((1,1),(1,0)), ((1,1),(1,2)), ((1,1),(2,1))]
    wire_net.set_data_path_state(occupy_path, True, communication_id, 0.)
    path_flag, transfer_path = schedule_strategy._find_check_path(communication_id)
    print(f"test case 1: {path_flag}, {transfer_path}")
    # test case 2
    occupy_path = [((0,1),(0,0))]
    wire_net.set_data_path_state(occupy_path, True, communication_id, 0.)
    path_flag, transfer_path = schedule_strategy._find_check_path(communication_id)
    print(f"test case 2: {path_flag}, {transfer_path}")
