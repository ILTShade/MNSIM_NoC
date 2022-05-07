#-*-coding:utf-8-*-
"""
@FileName:
    schedule.py
@Description:
    schedule class for behavior-driven simulation
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 21:20
"""
from mnsim_noc.utils.component import Component

class Schedule(Component):
    """
    schedule class for behavior-driven simulation
    """
    REGISTRY = "schedule"
    NAME = "behavior_driven"
    def __init__(self, communication_list):
        self.communication_list = communication_list
        self.wire_net = self.communication_list[0].wire_net

    def get_naive_path(self, communication):
        """
        get naive path
        """
        start_position = communication.input_tile.position
        end_position = communication.output_tile.position
        assert start_position != end_position
        current_position = [start_position[0], start_position[1]]
        path = []
        while True:
            path.append(tuple(current_position))
            # first left or right
            if current_position[1] != end_position[1]:
                current_position[1] += 1 if current_position[1] < end_position[1] else -1
            elif current_position[0] != end_position[0]:
                current_position[0] += 1 if current_position[0] < end_position[0] else -1
            else:
                break
        return [(path[i], path[i+1]) for i in range(len(path)-1)]

    def schedule(self, current_time):
        """
        schedule the communication
        """
        # get communication flag
        communication_ready_flag = [communication.check_communication_ready()
            for communication in self.communication_list
        ]
        # naive schedule
        transfer_path_list = []
        for i, ready_flag in enumerate(communication_ready_flag):
            if ready_flag:
                transfer_path = self.get_naive_path(self.communication_list[i])
                if self.wire_net.get_data_path_state(transfer_path):
                    transfer_path_list.append(transfer_path)
                    self.wire_net.set_data_path_state(transfer_path, True)
                    continue
            transfer_path_list.append(None)
        # set task
        for transfer_path, communication in zip(transfer_path_list, self.communication_list):
            communication.set_communication_task(current_time, transfer_path)
