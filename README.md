# MNSIM_NoC
## Requirements install
```
pip install -e .
```
## Simulator running
```
mnsim_noc --config examples/test.yaml
```

The format of the test.yaml file is as follows:
* image_num: the number of images to be simulated (default: 1)f
* tile_array_row: the number of rows in the tile array (default: 16)
* tile_array_col: the number of columns in the tile array (default: 16)
* input_buffer_size: the size of the input buffer in bits (default is 822400, 100KB)
* output_buffer_size: the size of the output buffer in bits (default is 822400, 100KB)
* band_width: the bandwidth of the link in bits/s (default is 1Gbps)
* task_config_path_list: the list of paths to the task configuration files
* mapping_strategy: the mapping strategy (default: naive)
* scheduling_strategy: the scheduling strategy (default: naive)
* transprent_flag: the flag to enable/disable the transparent mode (default: false)

For the task_config_path, should be end with pkl

## How to run experiments
```
mnsim_noc --config datas/base.yaml -M (for mapping strategy) -S (for scheduling strategy) -T (for transparent mode)
```

The flag -M, -S, -T can be used empty. if you want to change task_config_list, you can add as:

```
mnsim_noc --config datas/base.yaml -M -S -T --task datas/task1.pkl,datas/task2.pkl
```
tasks is split by comma.