# -*-coding:utf-8-*-
"""
@FileName:
    main.py
@Description:
    entry point
@CreateTime:
    2021/10/08 18:48
"""
from argparse import Action
import click
import pickle
from mnsim_noc.utils.yaml_io import read_yaml
from mnsim_noc.Array import BaseArray

@click.command(help="mnsim noc behavior driven simulation")
@click.option("--config", type=str, default="config.yaml", help="config file path")
@click.option("--task", type=str, help="task file path list")
@click.option("--mapping_strategy", "-M", type=str, help="mapping strategy")
@click.option("--schedule_strategy", "-S", type=str, help="schedule strategy")
@click.option("--transprent_flag", "-T", is_flag=True, default=False, help="transparent mode")
def main(config, task, mapping_strategy, schedule_strategy, transprent_flag):
    # load array config
    array_config = read_yaml(config)
    # load array config
    image_num = array_config.get("image_num", 1)
    tile_net_shape = (
        array_config.get("tile_array_row", 16),
        array_config.get("tile_array_col", 16)
    )
    buffer_size = (
        array_config.get("input_buffer_size", 32768),
        array_config.get("output_buffer_size", 32768)
    ) # default 32768 bits, 4KB
    band_width = array_config.get("band_width", 1) # default, 1Gbps
    mapping_strategy = array_config.get("mapping_strategy", "naive") \
        if mapping_strategy is None else mapping_strategy
    schedule_strategy = array_config.get("schedule_strategy", "naive") \
        if schedule_strategy is None else schedule_strategy
    transparent_flag = array_config.get("transparent_flag", False) \
        if transprent_flag is None else transprent_flag
    # overide config
    # load task config behavior list
    task_config_path_list = array_config.get("task_config_path_list", []) \
        if task is None else task.split(",")
    assert len(task_config_path_list) > 0, "task config path list is empty"
    task_behavior_list = []
    for i, task_config_path in enumerate(task_config_path_list):
        print(f"loading {i}th task config from {task_config_path} ")
        with open(task_config_path, "rb") as f:
            task_behavior_list.append(pickle.load(f))
    # create array
    array = BaseArray(
        task_behavior_list, image_num,
        tile_net_shape, buffer_size, band_width,
        mapping_strategy, schedule_strategy, transparent_flag
    )
    # array run and show config
    array.run()
    array.show_simulation_result()
