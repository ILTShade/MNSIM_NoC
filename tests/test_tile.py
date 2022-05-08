#-*-coding:utf-8-*-
"""
@FileName:
    test_tile.py
@Description:
    test tile, and as example
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 14:51
"""
from mnsim_noc.Tile import BaseTile

def test_tile():
    """
    test tile
    """
    # tile_behavior_cfg example
    tile_behavior_cfg = {
        "task_id": 0,
        "layer_id": 0,
        "tile_id": 0,
        "target_tile_id": [1],
        "dependence": [
            {
                "wait": [[1, 1, 0, 3, 9, 3, None, -1, -1]],
                "output": [[0, 0, 0, 3, 9, 3, None, 0, 0]],
                "drop": [],
                "latency": 1
            },
            {
                "wait": [[1, 1, 0, 3, 9, 3, None, -1, -1]],
                "output": [[0, 1, 0, 3, 9, 3, None, 0, 0]],
                "drop": [],
                "latency": 2
            },
            {
                "wait": [[1, 1, 0, 3, 9, 3, None, -1, -1]],
                "output": [[1, 0, 0, 3, 9, 3, None, 0, 0]],
                "drop": [],
                "latency": 3
            },
            {
                "wait": [[1, 1, 0, 3, 9, 3, None, -1, -1]],
                "output": [[1, 1, 0, 3, 9, 3, None, 0, 0]],
                "drop": [
                    [0, 0, 0, 3, 9, 3, None, -1, -1],
                    [0, 1, 0, 3, 9, 3, None, -1, -1],
                    [1, 0, 0, 3, 9, 3, None, -1, -1],
                    [1, 1, 0, 3, 9, 3, None, -1, -1],
                ],
                "latency": 4
            },
        ]
    }
    # init tile
    tile = BaseTile((0, 0), 2, (4096, 4096), tile_behavior_cfg)
    tile.input_buffer.set_start()
    # check for update
    current_time = 0
    while True:
        tile.update(current_time)
        current_time = tile.get_computation_end_time()
        # print(tile.get_computation_end_time())
        if current_time == float("inf"):
            break
    print(tile.get_computation_range())
