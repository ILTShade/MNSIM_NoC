#-*-coding:utf-8-*-
"""
@FileName:
    parallel_bandwidth.py
@Description:
    parallel for different bandwidth
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/09/21 15:02
"""

import os
import sys
import yaml

# read yaml file
def read_yaml(file_path):
    """
    read yaml file
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f.read())

# write yaml file
def write_yaml(file_path, data):
    """
    write yaml file
    """
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)


# init input bandwidth
bandwidth = int(sys.argv[1])
assert bandwidth % 2 == 0, f"bandwidth must be a multiple of 4, but got {bandwidth}"
# init new config for latency and throughput
latency_config = read_yaml("datas/imagenet_base.yaml")
latency_config["band_width"] = bandwidth
write_yaml(f"datas/bw{bandwidth}_imagenet_base.yaml", latency_config)
print(f"write datas/bw{bandwidth}_imagenet_base.yaml")

throughput_config = read_yaml("datas/throughput_imagenet_base.yaml")
throughput_config["band_width"] = bandwidth
write_yaml(f"datas/bw{bandwidth}_throughput_imagenet_base.yaml", throughput_config)
print(f"write datas/bw{bandwidth}_throughput_imagenet_base.yaml")

# run latency
for mapping, schedule in [
    ("snake", "naive"),
    ("preset_baseline", "naive"),
    ("preset_node_group", "naive_dynamic_all"),
    ("preset_node_group", "naive")
    ]:
    cmd = f"mnsim_noc" + \
    f" --config datas/bw{bandwidth}_imagenet_base.yaml" + \
    f" --task ~/nfs/mnsim_noc_date/datas/imagenet_vgg8.pkl" + \
    f" -M {mapping} -S {schedule}"
    if mapping == "preset_node_group" and schedule == "naive":
        cmd += " -T"
    print(f"Running {cmd}")
    os.system(cmd)
    # get result
    file_name = f"output_info_imagenet_vgg8.txt"
    with open(file_name, "r", encoding="utf-8") as f:
        lines = f.readlines()
        res = float(lines[0].strip("\n").split(" ")[-1])
    print(f"Done result: {res}")

# run latency
for mapping, schedule in [
    ("snake", "naive"),
    ("preset_baseline", "naive"),
    ("preset_node_group", "naive_dynamic_all"),
    ("preset_node_group", "naive")
    ]:
    cmd = f"mnsim_noc" + \
    f" --config datas/bw{bandwidth}_throughput_imagenet_base.yaml" + \
    f" --task ~/nfs/mnsim_noc_date/datas/imagenet_vgg8.pkl" + \
    f" -M {mapping} -S {schedule}"
    if mapping == "preset_node_group" and schedule == "naive":
        cmd += " -T"
    print(f"Running {cmd}")
    os.system(cmd)
    # get result
    file_name = f"output_info_imagenet_vgg8.txt"
    with open(file_name, "r", encoding="utf-8") as f:
        lines = f.readlines()
        res = float(lines[0].strip("\n").split(" ")[-1])
    print(f"Done result: {res}")
