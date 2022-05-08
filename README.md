# MNSIM_NoC
## Requirements Install
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
* input_buffer_size: the size of the input buffer in bits (default is 32768, 4KB)
* output_buffer_size: the size of the output buffer in bits (default is 32768, 4KB)
* band_width: the bandwidth of the link in bits/s (default is 1Gbps)
* task_config_path_list: the list of paths to the task configuration files

For the task_config_path, should be end with pkl