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
from mnsim_noc.Wire.wire_net import _get_map_key, _get_position_key

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
    def __init__(self, communication_list, wire_net):
        """
        initialize the schedule with cache
        """
        super(NaiveSchedule, self).__init__(communication_list, wire_net)
        self.path_cache = {} # cache the communication path

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
                    transfer_path, self.communication_list[index].transfer_data
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
        return, path_flag, path, path_str
        """
        transfer_path = self._get_naive_path(communication_id)
        # check if the path is avaliable
        path_flag = not self.wire_net.get_data_path_state(transfer_path)
        return path_flag, transfer_path

    def _get_naive_path(self, communication_id):
        """
        get naive path
        """
        # use cache path
        if str(communication_id) in self.path_cache:
            return self.path_cache[str(communication_id)]
        # ge path
        start_position = self.communication_list[communication_id].input_tile.position
        end_position = self.communication_list[communication_id].output_tile.position
        assert start_position != end_position, "start position and end position are the same"
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
        navie_path = [(path[i], path[i+1]) for i in range(len(path)-1)] # get wire
        # navie_path_str = [_get_map_key(path) for path in navie_path] # get map key
        self.path_cache[str(communication_id)] = navie_path # cache path
        return self.path_cache[str(communication_id)]

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
        start_node, end_node = _get_position_key(start_position), _get_position_key(end_position)
        path_flag = False
        # init all node info list, and the first start node
        all_node_info = {}
        for node, _ in self.wire_net.adjacency_dict.items():
            # the first item in list is distance from start_node, the second is the hops
            all_node_info[node] = [None, None]
        all_node_info[start_node][0] = 0
        # traverse the graph
        add_node_list = [start_node]
        while True:
            # TODO: perhaps limit the length
            next_node_list = []
            # get the next hops node
            for node in add_node_list:
                adjacency_node_list = self.wire_net.adjacency_dict[node]
                for adjacency_node in adjacency_node_list:
                    if all_node_info[adjacency_node][0] is not None:
                        continue
                    # add to next node list
                    all_node_info[adjacency_node] = [all_node_info[node][0] + 1, node]
                    next_node_list.append(adjacency_node)
            # check for output
            if end_node in next_node_list:
                # find end node, break
                path_flag = True
                break
            if len(next_node_list) == 0:
                # no new node, break
                path_flag = False
                break
            add_node_list = next_node_list
        # get path if path is found
        if path_flag:
            # get total path
            path = []
            current = end_node
            while True:
                path.append(self.wire_net.mapping_dict[current])
                if current == start_node:
                    break
                current = all_node_info[current][1]
            dynamic_path = [(path[i], path[i+1]) for i in range(len(path)-1)] # get wire
            return True, dynamic_path
        return False, None

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
