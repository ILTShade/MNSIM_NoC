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
from mnsim_noc.utils.component import Component

class Schedule(Component):
    """
    schedule class for behavior-driven simulation
    """
    REGISTRY = "schedule"
    def __init__(self, communication_list, wire_net):
        super(Schedule, self).__init__()
        self.communication_list = communication_list
        self.wire_net = wire_net

    @abc.abstractmethod
    def _get_transfer_path_list(self, communication_ready_flag, current_time):
        """
        get transfer path list, and transfer time list
        start communication in this method
        NO global optimization ,since there is priority
        """
        raise NotImplementedError

    def schedule(self, current_time):
        """
        schedule the communication
        """
        # get communication flag
        communication_ready_flag = [communication.check_communication_ready()
            for communication in self.communication_list
        ]
        # schedule and start communication
        self._get_transfer_path_list(communication_ready_flag, current_time)

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
        transfer_path = self.wire_net.find_data_path(start_position, end_position, False)
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
        transfer_path = self.wire_net.find_data_path(start_position, end_position, True)
        return transfer_path is not None, transfer_path

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
