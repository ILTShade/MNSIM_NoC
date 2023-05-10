#-*-coding:utf-8-*-
"""
@FileName:
    test_linear_programming.py
@Description:
    test linear programming
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2023/05/10 14:42
"""
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
from mnsim_noc.utils.linear_programming import ScheduleLinearProgramming


@pytest.mark.parametrize("config, task", [("examples/test.yaml", "examples/test.pkl")])
def test_schedule(config, task):
    """
    test schedule step for each communication
    """
    # load array config
    array_config = read_yaml(config)
    task_name_label = "test"
    image_num = array_config.get("image_num")
    noc_topology = array_config.get("noc_topology")
    tile_net_shape = (
        array_config.get("tile_array_row"),
        array_config.get("tile_array_col")
    )
    buffer_size = (
        array_config.get("input_buffer_size"),
        array_config.get("output_buffer_size")
    )
    band_width = array_config.get("band_width")
    path_generator = "naive"
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
        noc_topology, tile_net_shape, buffer_size, band_width,
        path_generator, mapping_strategy, schedule_strategy, transparent_flag
    )
    # init schedule
    assert len(array.output_behavior_list) == 1, \
        f"output behavior list is {array.output_behavior_list}, length is over 1"
    _, _, communication_list, wire_net = array.output_behavior_list[0]
    wire_net.set_transparent_flag(transparent_flag)
    # set up the linear programming
    linear_programming = ScheduleLinearProgramming(communication_list, wire_net)
