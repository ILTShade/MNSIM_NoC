#-*-coding:utf-8-*-
"""
@FileName:
    parallel_turn_model.py
@Description:
    parallel for turn model
    This script is used to run the program in parallel
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2023/05/04 17:40
"""
import sys
import subprocess

# init
path_generator = sys.argv[1]
assert path_generator in [
    "naive",
    "west_first", "north_last", "negative_first",
    "adaptive", "greedy", "dijkstra", "astar"
]

mapping_list = ["naive", "snake", "impact"]
schedule = "naive"
datasets = ["cifar"]
models = ["alexnet", "vgg8", "resnet18", "vgg16"]
for dataset in datasets:
    for mapping in mapping_list:
        for model in models:
            # run
            cmd = f"mnsim_noc" + \
                f" --config datas/{dataset}_base.yaml" + \
                f" --task ~/nfs/mnsim_noc_date/datas/{dataset}_{model}.pkl" + \
                f" -M {mapping} -S {schedule} -G {path_generator}"
            print(f"running latency {dataset} {model}: {mapping} {schedule}, {path_generator}")
            subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
            # get result
            file_name = f"output_info_{dataset}_{model}.txt"
            with open(file_name, "r", encoding="utf-8") as f:
                lines = f.readlines()
                res = lines[0].strip("\n").split(" ")
            print(f"\t{res[0]} second cost, latency is {res[1]} s")
