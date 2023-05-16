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
import os
import sys
import subprocess

solver_config_list = [
    "COPT,norm,float", # 6.31 s
    "ECOS,norm,float", # 62.2 s
    "ECOS_BB,norm,float", # 61.9 s
    "GUROBI,norm,float", # 12.3 s
    # "MOSEK,norm,float", # can not support vgg16
    # "SCS,norm,float", # can not support vgg16
    # "ECOS_BB,norm,integer", # time-consuming
    # "GUROBI,norm,integer", # 250 s
    # "MOSEK,norm,integer", # time-consuming
    "CBC,max,float", # 50.4 s
    "COPT,max,float", # 1.28 s
    "ECOS,max,float", # 36.3 s
    "ECOS_BB,max,float", # 36.3 s
    # "GLPK,max,float", # 4646 s # time-consuming
    # "GLPK_MI,max,float", # 1248 s # time-consuming
    "GUROBI,max,float", # 4.1 s
    "MOSEK,max,float", # 8.5 s
    "SCIPY,max,float", # 0.8 s
    "CBC,max,integer", # 115 s
    "COPT,max,integer", # 22.5 s
    # "ECOS_BB,max,integer", # time-consuming
    # "GLPK_MI,max,integer", # 1248 s # time-consuming
    "GUROBI,max,integer", # 5.7 s
    "MOSEK,max,integer", # 7.9 s
]
alpha_list = [float(i)/10 for i in range(0, 11, 1)]

# init
mapping = sys.argv[1]
mapping_list = ["naive", "snake", "impact"]
assert mapping in mapping_list

model = sys.argv[2]
models = ["alexnet", "vgg8", "resnet18", "vgg16"]
assert model in models

schedule = "naive"
dataset = "cifar"
for alpha in alpha_list:
    for solver_config in solver_config_list:
        beta = 1 - alpha
        path_generator = f"cvxopt@{alpha:.2f},{beta:.2f},{solver_config}"
        # run
        cmd = f"mnsim_noc" + \
            f" --config datas/{dataset}_base.yaml" + \
            f" --task ~/nfs/mnsim_noc_date/datas/{dataset}_{model}.pkl" + \
            f" -M {mapping} -S {schedule} -G {path_generator}"
        print(f"running latency {dataset} {model}: {mapping} {schedule}, {path_generator}")
        subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        # get result
        file_name = f"output_info_{dataset}_{model}_{mapping}_{schedule}_{path_generator}.txt"
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                lines = f.readlines()
                res = lines[0].strip("\n").split(" ")
            print(f"\t{res[0]} second cost, latency is {res[1]} s")
        else:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write("-1 -1")
            print(f"\t{file_name} not exists")
