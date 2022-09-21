#-*-coding:utf-8-*-
"""
@FileName:
    parallel_run.py
@Description:
    This script is used to run the program in parallel.
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/09/18 22:41
"""
import os
import sys

# init
mapping = sys.argv[1]
assert mapping in ["snake", "impact", "preset_baseline", "preset_node_group"]
schedule = sys.argv[2]
assert schedule in ["naive", "naive_dynamic_all"]

datasets = ["cifar", "imagenet"]
models = ["alexnet", "vgg8", "resnet18", "vgg16"]
for dataset in datasets:
    if dataset == "cifar":
        continue
    for model in models:
        if model == "alexnet":
            continue
        # run
        cmd = f"mnsim_noc" + \
            f" --config datas/throughput_{dataset}_base.yaml" + \
            f" --task ~/nfs/mnsim_noc_date/datas/{dataset}_{model}.pkl" + \
            f" -M {mapping} -S {schedule}"
        print(f"running throughput {dataset} {model}: {mapping} {schedule}")
        os.system(cmd)
        # get result
        file_name = f"output_info_{dataset}_{model}.txt"
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
            res = float(lines[0].strip("\n").split(" ")[-1])
        print(f"\t done result: {res}")
