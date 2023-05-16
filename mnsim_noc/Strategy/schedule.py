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
from mnsim_noc.utils.linear_programming import ScheduleLinearProgramming
from mnsim_noc.Wire.wire_net import _get_map_key

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
        # init hyper parameter
        # check for the path generator in DynamicPath and DynamicAll
        if isinstance(self, DynamicPathSchedule):
            self.max_len_ratio = 1.8
            self.branch_preset = 2
            self.logger.info(
                f"The ratio is {self.max_len_ratio}, and the branch preset is {self.branch_preset}"
            )
            assert self.path_generator in ["greedy", "dijkstra", "astar"], \
                "path generator should be greedy, dijkstra, astar for DynamicPathSchedule"
        # check for the path generator if starts with "cvxopt@" in LinearProgrammingSchedule
        if self.path_generator.startswith("cvxopt@"):
            # the path generator is in format of cvxopt@1,1,GUROBI,norm,float
            # first step, init the linear solver
            self.linear_solver = ScheduleLinearProgramming(
                self.communication_list, self.wire_net
            )
            # second step, set config and solve the problem
            solver_config = self.path_generator.split("@")[1]
            self.linear_solver.SOLVER_CONFIG = solver_config
            self.linear_solver.solve()
            self.logger.info(
                f"the optimal total transfer cost is {self.linear_solver.optimal_obj_total_transfer_cost}"
            )
            comm_schedule_ifo_list = self.linear_solver.parse_x(self.linear_solver.optimal_x)
            # last step, set the communication schedule into the wire net
            assert len(comm_schedule_ifo_list) == len(self.communication_list), \
                "communication schedule info list length is not equal to communication list length"
            for comm_schedule_info, comm in zip(comm_schedule_ifo_list, self.communication_list):
                start_position = comm.input_tile.position
                end_position = comm.output_tile.position
                cache_key = _get_map_key((start_position, end_position))
                self.wire_net.cvxopt_cache_dict[cache_key] = comm_schedule_info
                self.wire_net.cvxopt_index_cache[cache_key] = dict()
            self.wire_net._cvxopt_sort_dict()
            # finally
            self.logger.info("the communication schedule is set into the wire net")
            self.path_generator = "cvxopt"

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
                # update if the path generator is cvxopt
                if self.path_generator == "cvxopt":
                    self.wire_net._cvxopt_update_cache(
                        self.communication_list[index].input_tile.position,
                        self.communication_list[index].output_tile.position,
                        transfer_path_list[index],
                        self.communication_list[index].transfer_data
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
