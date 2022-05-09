#-*-coding:utf-8-*-
"""
@FileName:
    test_array.py
@Description:
    test array for behavior dirven
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 21:48
"""
from mnsim_noc.Array import BaseArray

def get_test_config():
    """
    get test config
    """
    # 2x2 conv, pooling, conv, element_sum, fc
    # conv1
    tile_behavior_cfg_conv1 = {
        "task_id": None,
        "layer_id": 0,
        "tile_id": 0,
        "target_tile_id": [1],
        "source_tile_id": [-1],
        "dependence": [
            {
                "wait": [[1, 1, 0, 3, 9, 3, None, None, -1, None]],
                "output": [[0, 0, 0, 3, 9, 3, None, 0, -1, 0]],
                "drop": [],
                "latency": 4
            },
            {
                "wait": [[1, 1, 0, 3, 9, 3, None, None, -1, None]],
                "output": [[0, 1, 0, 3, 9, 3, None, 0, -1, 0]],
                "drop": [],
                "latency": 2
            },
            {
                "wait": [[1, 1, 0, 3, 9, 3, None, None, -1, None]],
                "output": [[1, 0, 0, 3, 9, 3, None, 0, -1, 0]],
                "drop": [],
                "latency": 3
            },
            {
                "wait": [[1, 1, 0, 3, 9, 3, None, None, -1, None]],
                "output": [[1, 1, 0, 3, 9, 3, None, 0, -1, 0]],
                "drop": [
                    [0, 0, 0, 3, 9, 3, None, None, -1, None],
                    [0, 1, 0, 3, 9, 3, None, None, -1, None],
                    [1, 0, 0, 3, 9, 3, None, None, -1, None],
                    [1, 1, 0, 3, 9, 3, None, None, -1, None],
                ],
                "latency": 7
            },
        ]
    }
    # pooling1
    tile_behavior_cfg_pooling1 = {
        "task_id": None,
        "layer_id": 1,
        "tile_id": 1,
        "target_tile_id": [2, 3],
        "source_tile_id": [0],
        "dependence": [
            {
                "wait": [
                    [0, 0, 0, 3, 9, 3, None, 0, -1, 0],
                    [0, 1, 0, 3, 9, 3, None, 0, -1, 0],
                    [1, 0, 0, 3, 9, 3, None, 0, -1, 0],
                    [1, 1, 0, 3, 9, 3, None, 0, -1, 0],
                ],
                "output": [[0, 0, 0, 3, 9, 3, None, 1, -1, 1]],
                "latency": 9,
                "drop": [
                    [0, 0, 0, 3, 9, 3, None, 0, -1, 0],
                    [0, 1, 0, 3, 9, 3, None, 0, -1, 0],
                    [1, 0, 0, 3, 9, 3, None, 0, -1, 0],
                    [1, 1, 0, 3, 9, 3, None, 0, -1, 0],
                ],
            },
        ]
    }
    # conv2
    tile_behavior_cfg_conv2 = {
        "task_id": None,
        "layer_id": 2,
        "tile_id": 2,
        "target_tile_id": [3],
        "source_tile_id": [1],
        "dependence": [
            {
                "wait": [[0, 0, 0, 3, 9, 3, None, 1, -1, 1]],
                "output": [[0, 0, 0, 3, 9, 3, None, 2, -1, 2]],
                "latency": 7,
                "drop": [[0, 0, 0, 3, 9, 3, None, 1, -1, 1]],
            },
        ]
    }
    # element_sum
    tile_behavior_cfg_element_sum = {
        "task_id": None,
        "layer_id": 3,
        "tile_id": 3,
        "target_tile_id": [4],
        "source_tile_id": [1, 2],
        "dependence": [
            {
                "wait": [[0, 0, 0, 3, 9, 3, None, 1, -1, 1], [0, 0, 0, 3, 9, 3, None, 2, -1, 2]],
                "output": [[0, 0, 0, 3, 9, 3, None, 3, -1, 3]],
                "latency": 6,
                "drop": [[0, 0, 0, 3, 9, 3, None, 1, -1, 1], [0, 0, 0, 3, 9, 3, None, 2, -1, 2]],
            },
        ]
    }
    # fc
    tile_behavior_cfg_fc = {
        "task_id": None,
        "layer_id": 4,
        "tile_id": 4,
        "target_tile_id": [-1],
        "source_tile_id": [3],
        "dependence": [
            {
                "wait": [[0, 0, 0, 3, 9, 3, None, 3, -1, 3]],
                "output": [[0, 0, 0, 3, 9, 3, None, 4, -1, 4]],
                "latency": 5,
                "drop": [[0, 0, 0, 3, 9, 3, None, 3, -1, 3]],
            },
        ]
    }
    return [[tile_behavior_cfg_conv1, tile_behavior_cfg_pooling1,
        tile_behavior_cfg_conv2, tile_behavior_cfg_element_sum, tile_behavior_cfg_fc
    ]]

def test_array():
    """
    test array in behavior driven
    """
    array = BaseArray(get_test_config(), 2, (3, 3), (4096, 4096), 1, transparent_flag=True)
    array.run()