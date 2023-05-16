#-*-coding:utf-8-*-
"""
@FileName:
    base_time_slice_array.py
@Description:
    Base Array class
@CreateTime:
    2021/10/08 18:21
"""
import time
import bisect
import numpy as np
from mnsim_noc.utils.component import Component
from mnsim_noc.Strategy.mapping import Mapping
from mnsim_noc.Strategy.schedule import Schedule

class BaseArray(Component):
    """
    base array for behavior driven simulation
    """
    REGISTRY = "array"
    NAME = "behavior_driven"
    def __init__(self, task_name_label, task_behavior_list, image_num,
        noc_topology, tile_net_shape, buffer_size, band_width,
        mapping_strategy="naive", schedule_strategy="naive", transparent_flag=False,
        path_generator="naive"
    ):
        super(BaseArray, self).__init__()
        self.task_name_label = task_name_label
        # logging
        self.logger.info("Initializing the array")
        self.logger.info(f"\tThe task name label is {task_name_label}")
        self.logger.info(f"\tThere are {len(task_behavior_list)} tasks")
        for i, task_behavior in enumerate(task_behavior_list):
            self.logger.info(f"\t\tTask {i} need {len(task_behavior)} tiles")
        self.logger.info(f"\tThe image number is {image_num}")
        self.logger.info(f"\tThe noc topology is {noc_topology}")
        self.logger.info(f"\tThe tile net shape is {tile_net_shape}")
        self.logger.info(f"\tThe buffer size is {buffer_size}")
        self.logger.info(f"\tThe band width is {band_width}")
        self.logger.info(
            f"\tStrategy are {mapping_strategy}, {schedule_strategy}, {transparent_flag}"
        )
        self.logger.info(f"\tThe path generator is {path_generator}")
        # show the array
        self._get_behavior_number(task_behavior_list)
        # init
        self.mapping_strategy = Mapping.get_class_(mapping_strategy)(
            task_name_label, task_behavior_list, image_num,\
            noc_topology, tile_net_shape, buffer_size, band_width
        )
        # self.tile_list, self.communication_list, self.wire_net = \
        # self.mapping_strategy.mapping_net()
        self.output_behavior_list = self.mapping_strategy.mapping_net()
        # set transparent
        self.transparent_flag = transparent_flag
        self.schedule_strategy = schedule_strategy
        self.path_generator = path_generator
        # self.wire_net.set_transparent_flag(transparent_flag)
        # self.schedule_strategy = Schedule.get_class_(schedule_strategy)(
            # self.communication_list, self.wire_net
        # )
        # time point list
        self.image_num = image_num
        self.tile_net_shape = tile_net_shape

    def _get_behavior_number(self, task_behavior_list):
        """
        get the behavior number
        """
        tile_number = []
        communication_number = []
        computing_behavior_number = []
        communication_behavior_number = []
        for _, task_behavior in enumerate(task_behavior_list):
            # for tile number
            tile_number.append(len(task_behavior))
            # for the communication number and behavior number
            task_communication_number = 0
            task_computing_behavior_number = 0
            task_communication_behavior_number = 0
            for tile_behavior in task_behavior:
                task_computing_behavior_number += len(tile_behavior["dependence"])
                if tile_behavior["target_tile_id"] != [-1]:
                    task_communication_number += len(tile_behavior["target_tile_id"])
                    task_communication_behavior_number += \
                        len(tile_behavior["dependence"]) * \
                        len(tile_behavior["target_tile_id"])
            communication_number.append(task_communication_number)
            computing_behavior_number.append(task_computing_behavior_number)
            communication_behavior_number.append(task_communication_behavior_number)
        # logger
        self.logger.info(
            f"In total, {sum(tile_number)} tiles," + \
            f" {sum(communication_number)} communications," + \
            f" {sum(computing_behavior_number)} computing behaviors," + \
            f" {sum(communication_behavior_number)} communication behaviors"
        )
        for i in range(len(task_behavior_list)):
            self.logger.info(
                f"\tTask {i} has {tile_number[i]} tiles," + \
                f" {communication_number[i]} communications," + \
                f" {computing_behavior_number[i]} computing behaviors," + \
                f" {communication_behavior_number[i]} communication behaviors"
            )

    def run(self):
        """
        run the array
        """
        output_list = []
        for _, (fitness, tile_list, communication_list, wire_net) in \
            enumerate(self.output_behavior_list):
            # init wire net and schedule
            wire_net.set_transparent_flag(self.transparent_flag)
            schedule_strategy = Schedule.get_class_(self.schedule_strategy)(
                communication_list, wire_net, self.path_generator
            )
            # init current time and time point list
            current_time = 0.
            time_point_list = []
            # get the adjacency list saved in predecessors and successors
            tile_predecessors, tile_successors, comm_predecessors, comm_successors = \
                self.mapping_strategy.get_adjacency_list(
                    tile_list, communication_list
                )
            # record all the communication end time in the original order
            communication_end_time_list = [float("inf")] * len(communication_list)
            communication_schedule_flag = [False] * len(communication_list)
            # record all tile flag
            tile_end_time_list = [float("inf")] * len(tile_list)
            tile_update_flag = [False] * len(tile_list)
            # the start buffer should be set to true
            for tile_id, tile in enumerate(tile_list):
                if tile.input_buffer.start_flag:
                    tile_update_flag[tile_id] = True
            sorted_finish_time_list = []
            start_time = time.time()
            while True:
                # running the data in the optimal order
                # first, update part of the communication which can be done in current time
                comm_id_list = [
                    i for i, comm_end_time in enumerate(communication_end_time_list) \
                    if comm_end_time <= current_time
                ]
                for comm_id in comm_id_list:
                    # 1.1 update the communication, and end time
                    communication_list[comm_id].update(current_time)
                    communication_end_time_list[comm_id] = float("inf")
                    # 1.2 add to the schedule flag list
                    communication_schedule_flag[comm_id] = True
                    # 1.3 set successors tile update flag
                    for tile_id in comm_successors[comm_id]:
                        tile_update_flag[tile_id] = True
                    # 1.4 pop one element from the sorted finish time list
                    sorted_finish_time_list.pop(0)
                # second, update part of the tile which can be done in current time
                tile_id_list = [
                    i for i, tile_end_time in enumerate(tile_end_time_list) \
                    if tile_end_time <= current_time
                ]
                for tile_id in tile_id_list:
                    # 2.1 add to the update flag list
                    tile_update_flag[tile_id] = True
                    # 2.2 set predecessors and successors comm schedule flag
                    for comm_id in tile_predecessors[tile_id]:
                        communication_schedule_flag[comm_id] = True
                    for comm_id in tile_successors[tile_id]:
                        communication_schedule_flag[comm_id] = True
                    # 2.3 pop one element from the sorted finish time list
                    sorted_finish_time_list.pop(0)
                # third, update based on the update flag
                # achieve no redundant update
                tile_id_list = [i for i, flag in enumerate(tile_update_flag) if flag]
                for tile_id in tile_id_list:
                    before_finish_time = tile_end_time_list[tile_id]
                    # 3.1 update the tile
                    tile_list[tile_id].update(current_time)
                    # 3.2 update the end tile
                    tile_end_time_list[tile_id] = tile_list[tile_id].get_computation_end_time()
                    # 3.3 update the update flag, only update only state changes
                    tile_update_flag[tile_id] = False
                    # 3.4 add to the sorted finish time list
                    after_finish_time = tile_end_time_list[tile_id]
                    if after_finish_time < float("inf") and \
                        after_finish_time != before_finish_time:
                        bisect.insort(
                            sorted_finish_time_list, tile_end_time_list[tile_id]
                        )

                # schedule for the path
                task_comm_id_list = \
                    schedule_strategy.schedule(current_time, communication_schedule_flag)
                # fourth, update the communication which is set tasks
                for comm_id in task_comm_id_list:
                    # 4.1 update the communication end time
                    communication_end_time_list[comm_id] = \
                        communication_list[comm_id].get_communication_end_time()
                    # 4.2 set the update flag of the tile successors as True
                    for tile_id in comm_predecessors[comm_id]:
                        tile_update_flag[tile_id] = True
                    # 4.3 add to the sorted finish time list
                    bisect.insort(
                        sorted_finish_time_list, communication_end_time_list[comm_id]
                    )
                # 4.3 set the communication schedule flag as False if in running or done
                comm_id_list = [i for i, flag in enumerate(communication_schedule_flag) if flag]
                for comm_id in comm_id_list:
                    comm = communication_list[comm_id]
                    if comm.running_state or \
                        comm.number_done_communication == comm.number_total_communication:
                        communication_schedule_flag[comm_id] = False

                # get next time
                next_time = sorted_finish_time_list[0] if sorted_finish_time_list else float("inf")
                # check if the simulation is over
                assert next_time > current_time
                current_time = next_time
                if current_time == float("inf"):
                    break
                time_point_list.append(current_time)
            end_time = time.time()
            output_list.append((end_time - start_time, time_point_list[-1]/1e6))
            # check if the simulation is over
            self.check_finish(tile_list, communication_list, wire_net)
            # log info
            self.logger.info(
                f"For the {_}th: {fitness}, \033[1;31;40m{time_point_list[-1]/1e6:.3f}\033[0m" + \
                f" ms, {end_time - start_time:.3f} seconds"
            )
            # log communication amount
            # energy_bit = 5.445 + 0.43 # pJ / bit
            # total_transfer_bits = wire_net.get_communication_amounts()/1e6 # M bits
            # self.logger.info(f"Communication amounts: {total_transfer_bits:.2f} M bits")
            # self.logger.info(f"Energy consumption: {total_transfer_bits*energy_bit/1e3:.3f} mJ")
            # # get running rate for all wires
            # horizontal_rate, vertical_rate = wire_net.get_running_rate(time_point_list[-1])
            # rate_sum = np.sum(horizontal_rate) + np.sum(vertical_rate)
            # self.logger.info(f"total running rate: {rate_sum}")
        # save for the output
        output_list = np.array(output_list)
        file_name = f"output_info_{self.task_name_label}" + \
            f"_{self.mapping_strategy.NAME}_{self.schedule_strategy}_{self.path_generator}.txt"
        np.savetxt(file_name, output_list, fmt="%.3f")
        self.logger.info(f"The output info is saved in {file_name}")
        # get min index
        # min_index = np.argsort(output_list[:, 1])[0]
        # self.logger.info(
        #     f"The min index is {min_index}, and latency is {output_list[min_index, 1]}"
        # )

    def check_finish(self, tile_list, communication_list, wire_net):
        """
        check if the simulation is over and right
        """
        # check if the tile is finished
        for tile in tile_list:
            tile.check_finish()
        # check if the communication is finished
        for communication in communication_list:
            communication.check_finish()
        # check if the wire net is finished
        wire_net.check_finish()
