#-*-coding:utf-8-*-
"""
@FileName:
    parallel_communication_amounts.py
@Description:
    This script is used to run the program in parallel.
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/09/23 16:43
"""
import os
import sys

# init
mapping = sys.argv[1]
assert mapping in ["snake", "impact", "preset_baseline", "preset_node_group"]

datasets = ["cifar", "imagenet"]
models = ["alexnet", "vgg8", "resnet18", "vgg16"]
for dataset in datasets:
    for model in models:
        # get results
        cmd = f"mnsim_noc " + \
            f"--config datas/{dataset}_base.yaml " + \
            f"--task ~/nfs/mnsim_noc_date/datas/{dataset}_{model}.pkl " + \
            f"-M {mapping} -S naive"
        print(f"running throughput {dataset} {model}: {mapping}")
        os.system(cmd)
