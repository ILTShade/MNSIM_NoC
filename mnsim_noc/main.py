# -*-coding:utf-8-*-
"""
@FileName:
    main.py
@Description:
    entry point
@CreateTime:
    2021/10/08 18:48
"""
import click
import pickle
from mnsim_noc.utils.yaml_io import read_yaml
from mnsim_noc.Array import BaseArray

@click.command(help="mnsim noc behavior driven simulation")
@click.option("--config", type=str, default="config.yaml", help="config file path")
def main(config):
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
    mapping_strategy = array_config.get("mapping_strategy", "naive")
    schedule_strategy = array_config.get("schedule_strategy", "naive")
    transparent_flag = array_config.get("transparent_flag", False)
    # load task config behavior list
    task_config_path_list = array_config.get("task_config_path_list", [])
    assert len(task_config_path_list) > 0, "task config path list is empty"
    task_behavior_list = []
    for task_config_path in task_config_path_list:
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
