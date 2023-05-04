# -*-coding:utf-8-*-
"""
@FileName:
    main.py
@Description:
    entry point
@CreateTime:
    2021/10/08 18:48
"""
import os
import pickle
from line_profiler import LineProfiler

import click

from mnsim_noc.Array import BaseArray
from mnsim_noc.Strategy.schedule import Schedule
from mnsim_noc.Tile.base_tile import BaseTile
from mnsim_noc.Communication.base_communication import BaseCommunication
from mnsim_noc.utils.yaml_io import read_yaml


@click.command(help="mnsim noc behavior driven simulation")
@click.option("--config", type=str, default="config.yaml", help="config file path")
@click.option("--task", type=str, help="task file path list")
@click.option("--mapping_strategy", "-M", type=str, help="mapping strategy")
@click.option("--schedule_strategy", "-S", type=str, help="schedule strategy")
@click.option("--transparent_flag", "-T", is_flag=True, default=False, help="transparent mode")
@click.option("--profile_flag", "-P", is_flag=True, default=False, help="profile mode")
@click.option("--path_generator", "-G", type=str, help="path generator")
def main(
    config,
    task, mapping_strategy, schedule_strategy, transparent_flag,
    profile_flag, path_generator
    ):
    """
    main function
    """
    # load array config
    array_config = read_yaml(config)
    # load array config
    image_num = array_config.get("image_num", 1)
    noc_topology = array_config.get("noc_topology", "mesh")
    tile_net_shape = (
        array_config.get("tile_array_row", 16),
        array_config.get("tile_array_col", 16)
    )
    buffer_size = (
        array_config.get("input_buffer_size", 822400),
        array_config.get("output_buffer_size", 822400)
    ) # default 822400 bits
    band_width = array_config.get("band_width", 1) # default, 1Gbps
    mapping_strategy = array_config.get("mapping_strategy", "naive") \
        if mapping_strategy is None else mapping_strategy
    schedule_strategy = array_config.get("schedule_strategy", "naive") \
        if schedule_strategy is None else schedule_strategy
    transparent_flag = array_config.get("transparent_flag", False) \
        if transparent_flag is None else transparent_flag
    path_generator = array_config.get("path_generator", "naive") \
        if path_generator is None else path_generator
    # override config
    # load task config behavior list
    task_config_path_list = array_config.get("task_config_path_list", []) \
        if task is None else task.split(",")
    assert len(task_config_path_list) > 0, "task config path list is empty"
    task_behavior_list = []
    task_name_label = []
    for i, task_config_path in enumerate(task_config_path_list):
        print(f"loading {i}th task config from {task_config_path} ")
        with open(task_config_path, "rb") as f:
            task_behavior_list.append(pickle.load(f))
        task_name_label.append(os.path.splitext(os.path.basename(task_config_path))[0])
    task_name_label = ",".join(task_name_label)
    # print(f"task name label: {task_name_label}")
    # create array
    array = BaseArray(
        task_name_label,
        task_behavior_list, image_num,
        noc_topology, tile_net_shape, buffer_size, band_width,
        mapping_strategy, schedule_strategy, transparent_flag,
        path_generator
    )
    # array run and show config
    if not profile_flag:
        array.run()
    else:
        lp = LineProfiler()
        # main function for profiling, schedule and update
        lp.add_function(Schedule.schedule)
        lp.add_function(Schedule.get_class_(schedule_strategy)._get_transfer_path_list)
        lp.add_function(Schedule.get_class_(schedule_strategy)._find_check_path)
        lp.add_function(BaseTile.update)
        lp.add_function(BaseCommunication.update)
        # array run
        lp_wrapper = lp(array.run)
        lp_wrapper()
        lp.print_stats()
