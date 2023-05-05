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
import abc
import math
from mnsim_noc.utils.component import Component

class Schedule(Component):
    """
    schedule class for behavior-driven simulation
    """
    REGISTRY = "schedule"
    def __init__(self, communication_list, wire_net, path_generator):
        super(Schedule, self).__init__()
        self.communication_list = communication_list
        self.wire_net = wire_net
        self.path_generator = path_generator
        # naive for X-Y without through the border
        # adaptive for X-Y with through the border when torus
        # when the noc topology is mesh, there should be no diff in naive and adaptive
        # assert self.path_generator in ["naive", "adaptive", "dijkstra"], \
            # "path generator should be naive, adaptive, dijkstra"
        # init hyper parameter
        self.max_len_ratio = 1.8
        self.branch_preset = 2
        self.logger.info(
            f"The ratio is {self.max_len_ratio}, and the branch preset is {self.branch_preset}"
        )

    @abc.abstractmethod
    def _get_transfer_path_list(self, communication_ready_flag, current_time):
        """
        get transfer path list, and transfer time list
        start communication in this method
        NO global optimization ,since there is priority
        """
        raise NotImplementedError

    def schedule(self, current_time, communication_schedule_flag):
        """
        schedule the communication
        """
        # get communication flag, filter by schedule flag
        communication_ready_flag = [
            self.communication_list[comm_id].check_communication_ready() if schedule_flag else False
            for comm_id, schedule_flag in enumerate(communication_schedule_flag)
        ]
        # schedule and start communication
        return self._get_transfer_path_list(communication_ready_flag, current_time)

class NaiveSchedule(Schedule):
    """
    naive schedule class for behavior-driven simulation
    """
    NAME = "naive"
    def _get_transfer_path_list(self, communication_ready_flag, current_time):
        """
        get transfer path list
        """
        # naive schedule template
        assert len(communication_ready_flag) == len(self.communication_list), \
            "communication ready flag length is not equal to communication list length"
        transfer_path_list = [None] * len(self.communication_list)
        transfer_time_list = [None] * len(self.communication_list)
        # based on the priority, no all wire state
        # get sorted index and fused into communication ready flag
        sorted_index = self._get_sorted_index()
        sorted_index = list(filter(lambda x: communication_ready_flag[x], sorted_index))
        # output the task_comm_id_list
        task_comm_id_list = []
        # JUDGE
        for index in sorted_index:
            path_flag, transfer_path = self._find_check_path(index)
            if path_flag:
                # add transfer path to list
                transfer_path_list[index] = transfer_path
                # set transfer time
                transfer_time_list[index] = self.wire_net.get_wire_transfer_time(
                    transfer_path_list[index], self.communication_list[index].transfer_data
                )
                # start task
                self.communication_list[index].set_communication_task(
                    current_time, transfer_path_list[index], transfer_time_list[index]
                )
                # add to list
                task_comm_id_list.append(index)
        return task_comm_id_list

    def _get_sorted_index(self):
        """
        get sorted index based on the priority
        for the dynamic priority, naive is the default index
        """
        return list(range(len(self.communication_list)))

    def _find_check_path(self, communication_id):
        """
        find and check if there is a path for communication id
        naive path find
        return, path_flag, path, path_str
        """
        # get start and end
        start_position = self.communication_list[communication_id].input_tile.position
        end_position = self.communication_list[communication_id].output_tile.position
        assert start_position != end_position, "start position and end position are the same"
        # find path base on the path generator
        transfer_path = self.wire_net.find_data_path_cate(
            start_position, end_position, self.path_generator
        )
        if transfer_path is None:
            return False, None
        transfer_path_flag = not self.wire_net.get_data_path_state(transfer_path)
        return transfer_path_flag, transfer_path

class DynamicPrioritySchedule(NaiveSchedule):
    """
    dynamic priority schedule
    """
    NAME = "naive_dynamic_priority"
    def _get_sorted_index(self):
        """
        get sorted index based on the communication rate
        """
        done_rate_list = [
            (self.communication_list[i].get_done_communication_rate(), i)
            for i in range(len(self.communication_list))
        ]
        sorted_done_rate_list = sorted(done_rate_list, key=lambda x: x[0], reverse=False)
        sorted_index = [i[1] for i in sorted_done_rate_list]
        return sorted_index

class DynamicPathSchedule(NaiveSchedule):
    """
    dynamic path
    the communication path is not fixed, find the optimal design
    """
    NAME = "naive_dynamic_path"
    def _find_check_path(self, communication_id):
        """
        find and check if there is a dynamic path for communication id
        """
        # get start and end
        start_position = self.communication_list[communication_id].input_tile.position
        end_position = self.communication_list[communication_id].output_tile.position
        assert start_position != end_position, "start position and end position are the same"
        transfer_path = self.wire_net.find_data_path_cate(
            start_position, end_position, self.path_generator
        )
        # check if there are transfer path
        if transfer_path is None:
            return False, None
        # check for if the path is valid
        transfer_path_flag = not self.wire_net.get_data_path_state(transfer_path)
        if not transfer_path_flag:
            return transfer_path_flag, transfer_path
        # check for the path length, adaptive is the base
        naive_path = self.wire_net.find_data_path_cate(
            start_position, end_position, "adaptive"
        )
        max_path_len = math.floor(max(
            self.max_len_ratio * len(naive_path), # ratio for time
            len(naive_path) + self.branch_preset # branch for start node and end node
        ))
        return len(transfer_path) <= max_path_len, transfer_path

class DynamicAllSchedule(DynamicPrioritySchedule, DynamicPathSchedule):
    """
    dynamic priority and dynamic path both
    """
    NAME = "naive_dynamic_all"
    def _get_sorted_index(self):
        """
        get sorted index based on the communication rate
        """
        return DynamicPrioritySchedule._get_sorted_index(self)

    def _find_check_path(self, communication_id):
        """
        find and check if there is a path for communication id
        """
        return DynamicPathSchedule._find_check_path(self, communication_id)
