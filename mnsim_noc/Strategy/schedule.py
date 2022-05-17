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
from mnsim_noc.Wire.wire_net import _get_map_key

class Schedule(Component):
    """
    schedule class for behavior-driven simulation
    """
    REGISTRY = "schedule"
    def __init__(self, communication_list, wire_net):
        super(Schedule, self).__init__()
        self.communication_list = communication_list
        self.wire_net = wire_net
        self.all_wire_state = {}

    @abc.abstractmethod
    def _get_transfer_path_list(self, communication_ready_flag):
        """
        get transfer path list, and transfer time list
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
        transfer_path_list, transfer_time_list = \
            self._get_transfer_path_list(communication_ready_flag)
        # set task
        for transfer_path, transfer_time, communication in \
            zip(transfer_path_list, transfer_time_list, self.communication_list):
            communication.set_communication_task(current_time, transfer_path, transfer_time)

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

    def _get_transfer_path_list(self, communication_ready_flag):
        """
        get transfer path list
        """
        # naive schedule
        transfer_path_list = []
        transfer_time_list = []
        # get used wire state
        for i, ready_flag in enumerate(communication_ready_flag):
            if ready_flag:
                transfer_path, transfer_path_str = self._get_naive_path(i)
                self.wire_net.get_all_wire_state(self.all_wire_state, transfer_path_str)
        # judge
        for i, ready_flag in enumerate(communication_ready_flag):
            if ready_flag:
                transfer_path, transfer_path_str = self._get_naive_path(i)
                if not any([self.all_wire_state[key] for key in transfer_path_str]):
                    # add transfer path to list
                    transfer_path_list.append(transfer_path)
                    # set transfer time
                    transfer_time_list.append(
                        self.wire_net.get_wire_transfer_time(
                            transfer_path, self.communication_list[i].transfer_data
                        )
                    )
                    # update all wire state
                    for key in transfer_path_str:
                        self.all_wire_state[key] = not self.wire_net.transparent_flag
                    continue
            transfer_path_list.append(None)
            transfer_time_list.append(None)
        return transfer_path_list, transfer_time_list

    def _get_naive_path(self, i):
        """
        get naive path
        """
        # use cache path
        if str(i) in self.path_cache:
            return self.path_cache[str(i)]
        # ge path
        start_position = self.communication_list[i].input_tile.position
        end_position = self.communication_list[i].output_tile.position
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
        navie_path = [(path[i], path[i+1]) for i in range(len(path)-1)] # get wire
        navie_path_str = [_get_map_key(path) for path in navie_path] # get map key
        self.path_cache[str(i)] = (navie_path, navie_path_str) # cache path
        return self.path_cache[str(i)]

class ParallelSchedule(NaiveSchedule):
    """
    parallel schedule:
    use all wire inside the rectangle to transfer data
    suppose m is bigger than n
        then origin time is m + n
        and the parallel schedule time is (1+1/2+...+1/n)+(m-n)/(2*n+1)
    """
    NAME = "parallel"
    def __init__(self, communication_list, wire_net):
        """
        initialize the schedule with additional parallel cache
        """
        super(ParallelSchedule, self).__init__(communication_list, wire_net)
        self.parallel_path_cache = {} # cache the parallel communication path

    def _get_transfer_path_list(self, communication_ready_flag):
        """
        get transfer path list
        """
        # naive schedule
        transfer_path_list = []
        transfer_time_list = []
        # get used wire state
        for i, ready_flag in enumerate(communication_ready_flag):
            if ready_flag:
                transfer_path, transfer_path_str, _ = self._get_parallel_path(i)
                self.wire_net.get_all_wire_state(self.all_wire_state, transfer_path_str)
        # judge
        for i, ready_flag in enumerate(communication_ready_flag):
            if ready_flag:
                naive_transfer_path, _ = self._get_naive_path(i)
                transfer_path, transfer_path_str, scale = self._get_parallel_path(i)
                if not any([self.all_wire_state[key] for key in transfer_path_str]):
                    # add transfer path to list
                    transfer_path_list.append(transfer_path)
                    # set transfer time
                    transfer_time_list.append(
                        scale * self.wire_net.get_wire_transfer_time(
                            naive_transfer_path, self.communication_list[i].transfer_data
                        )
                    )
                    # update all wire state
                    for key in transfer_path_str:
                        self.all_wire_state[key] = not self.wire_net.transparent_flag
                    continue
            transfer_path_list.append(None)
            transfer_time_list.append(None)
        return transfer_path_list, transfer_time_list

    def _get_parallel_path(self, comm_id):
        """
        get parallel path
        """
        # use cache path
        if str(comm_id) in self.parallel_path_cache:
            return self.parallel_path_cache[str(comm_id)]
        # get parallel path
        start_position = self.communication_list[comm_id].input_tile.position
        end_position = self.communication_list[comm_id].output_tile.position
        assert start_position != end_position, \
            f"start position {start_position} is equal to end position {end_position}"
        # get minx, miny, maxx, maxy
        minx, maxx = \
            min(start_position[0], end_position[0]), max(start_position[0], end_position[0])
        miny, maxy = \
            min(start_position[1], end_position[1]), max(start_position[1], end_position[1])
        # get all wire inside the rectangle
        parallel_path = []
        for i in range(minx, maxx+1):
            for j in range(miny, maxy):
                parallel_path.append(((i,j),(i,j+1)))
        for i in range(minx, maxx):
            for j in range(miny, maxy+1):
                parallel_path.append(((i,j),(i+1,j)))
        # get map key
        parallel_path_str = [_get_map_key(path) for path in parallel_path]
        # get scale
        m = max(maxx-minx, maxy-miny)
        n = min(maxx-minx, maxy-miny)
        if n == 0:
            scale = 1
        else:
            s = sum([1/i for i in range(1, n+1)])
            scale = (s + (m-n)/(2*n+1))/(m+n)
        self.parallel_path_cache[str(comm_id)] = (parallel_path, parallel_path_str, scale)
        return self.parallel_path_cache[str(comm_id)]
