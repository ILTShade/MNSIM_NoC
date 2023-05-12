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
import numpy as np
import cvxpy as cp

from mnsim_noc.Array import BaseArray
from mnsim_noc.Strategy import Schedule
from mnsim_noc.utils.yaml_io import read_yaml
from mnsim_noc.utils.linear_programming import ScheduleLinearProgramming

# @pytest.mark.parametrize("config, task", [("datas/cifar_base.yaml", "/home/sunhanbo/nfs/mnsim_noc_date/datas/.pkl")])
@pytest.mark.parametrize("config, task", [("examples/test.yaml", "examples/test.pkl")])
@pytest.mark.parametrize("solver", cp.installed_solvers())
def test_schedule(config, task, solver):
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
    linear_programming.B[:,0] = linear_programming.B[:,0] / 4
    linear_programming.solver = solver
    linear_programming.solve()
    comm_schedule_info_list = linear_programming.parse_x(linear_programming.optimal_x)
    # show the result communication info
    print("-"*20)
    print(f"the optimal total transfer cost is {linear_programming.optimal_obj_total_transfer_cost}")
    optimal_value2 = linear_programming.optimal_obj_single_wire
    optimal_value2 = optimal_value2[np.abs(optimal_value2) < linear_programming.epsilon]
    print(f"the optimal single wire is: {optimal_value2}")
    print(f"the optimal object value is {linear_programming.optimal_obj_in_total}")
    for comm_id, comm_schedule_info in enumerate(comm_schedule_info_list):
        print(f"communication {comm_id} schedule info:")
        for path_id, (path, path_cost) in enumerate(comm_schedule_info):
            print(f"path {path_id}: {path}, cost: {path_cost}")
