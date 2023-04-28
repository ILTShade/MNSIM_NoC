#-*-coding:utf-8-*-
"""
@FileName:
    test_communication.py
@Description:
    test communication behavior-driven
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 19:01
"""
from mnsim_noc.Tile import BaseTile
from mnsim_noc.Wire import WireNet
from mnsim_noc.Communication import BaseCommunication

def test_communication():
    """
    test communication behavior-driven
    """
    # for tile 1
    tile_behavior_cfg_1 = {
        "task_id": 0,
        "layer_id": 0,
        "tile_id": 0,
        "target_tile_id": [1],
        "source_tile_id": [-1],
        "dependence": [
            {
                "wait": [[0, 0, 0, 3, 9, 3, None, None, -1, None]],
                "output": [[0, 0, 0, 3, 9, 3, None, 0, -1, 0]],
                "latency": 1,
                "drop": [[0, 0, 0, 3, 9, 3, None, None, -1, None]]
            },
            {
                "wait": [[0, 1, 0, 3, 9, 3, None, None, -1, None]],
                "output": [[0, 1, 0, 3, 9, 3, None, 0, -1, 0]],
                "latency": 100,
                "drop": [[0, 1, 0, 3, 9, 3, None, None, -1, None]]
            },
        ]
    }
    tile_1 = BaseTile((0, 0), 2, (4096, 4096), tile_behavior_cfg_1)
    # for tile 2
    tile_behavior_cfg_2 = {
        "task_id": 0,
        "layer_id": 1,
        "tile_id": 1,
        "target_tile_id": [-1],
        "source_tile_id": [0],
        "dependence": [
            {
                "wait": [[0, 0, 0, 3, 9, 3, None, 0, -1, 0]],
                "output": [[0, 0, 0, 3, 9, 3, None, 1, -1, 1]],
                "latency": 1,
                "drop": [[0, 0, 0, 3, 9, 3, None, 0, -1, 0]]
            },
            {
                "wait": [[0, 1, 0, 3, 9, 3, None, 0, -1, 0]],
                "output": [[0, 1, 0, 3, 9, 3, None, 1, -1, 1]],
                "latency": 1,
                "drop": [[0, 1, 0, 3, 9, 3, None, 0, -1, 0]]
            },
        ]
    }
    tile_2 = BaseTile((0, 1), 2, (4096, 4096), tile_behavior_cfg_2)
    # wire net
    wire_net = WireNet((2, 2), 10)
    # for communication
    communication_1 = BaseCommunication(tile_1, tile_2, wire_net)
    # check
    current_time = 0
    while True:
        # running data
        tile_1.update(current_time)
        communication_1.update(current_time)
        tile_2.update(current_time)
        # map communication schedule
        if communication_1.check_communication_ready():
            transfer_path = [((0, 0), (0, 1))]
        else:
            transfer_path = None
        communication_1.set_communication_task(current_time, transfer_path, 2.7)
        # modify current time
        current_time = min([
            tile_1.get_computation_end_time(),
            communication_1.get_communication_end_time(),
            tile_2.get_computation_end_time()
        ])
        if current_time == float("inf"):
            break

    print(tile_1.get_computation_range())
    print(tile_2.get_computation_range())
    print(communication_1.get_communication_range())
