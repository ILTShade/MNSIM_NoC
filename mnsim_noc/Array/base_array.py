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
        tile_net_shape, buffer_size, band_width,
        mapping_strategy="naive", schedule_strategy="naive", transparent_flag=False
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
        self.logger.info(f"\tThe tile net shape is {tile_net_shape}")
        self.logger.info(f"\tThe buffer size is {buffer_size}")
        self.logger.info(f"\tThe band width is {band_width}")
        self.logger.info(
            f"\tStrategy are {mapping_strategy}, {schedule_strategy}, {transparent_flag}"
        )
        # show the array
        self._get_behavior_number(task_behavior_list)
        # init
        self.mapping_strategy = Mapping.get_class_(mapping_strategy)(
            task_name_label, task_behavior_list, image_num, tile_net_shape, buffer_size, band_width
        )
        # self.tile_list, self.communication_list, self.wire_net = \
        # self.mapping_strategy.mapping_net()
        self.output_behavior_list = self.mapping_strategy.mapping_net()
        # set transparent
        self.transparent_flag = transparent_flag
        self.schedule_strategy = schedule_strategy
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
                communication_list, wire_net
            )
            # init current time and time point list
            current_time = 0.
            time_point_list = []
            update_module = self.mapping_strategy.get_update_order(
                tile_list, communication_list
            )
            start_time = time.time()
            while True:
                # running the data
                for module in update_module:
                    module.update(current_time)
                # schedule for the path
                schedule_strategy.schedule(current_time)
                # get next time
                next_time = min([
                    min([tile.get_computation_end_time() for tile in tile_list]),
                    min([
                        communication.get_communication_end_time()
                        for communication in communication_list
                    ])
                ])
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
            self.logger.info(f"For the {_}th: {fitness}, {time_point_list[-1]/1e6:.3f}")
            # log communication amount
            energy_bit = 5.445 + 0.43 # pJ / bit
            total_transfer_bits = wire_net.get_communication_amounts()/1e6 # M bits
            self.logger.info(f"Communication amounts: {total_transfer_bits:.2f} M bits")
            self.logger.info(f"Energy consumption: {total_transfer_bits*energy_bit/1e3:.3f} mJ")
            # get running rate for all wires
            horizontal_rate, vertical_rate = wire_net.get_running_rate(time_point_list[-1])
            rate_sum = np.sum(horizontal_rate) + np.sum(vertical_rate)
            self.logger.info(f"total running rate: {rate_sum}")
        # save for the output
        output_list = np.array(output_list)
        file_name = f"output_info_{self.task_name_label}.txt"
        np.savetxt(file_name, output_list, fmt="%.3f")
        self.logger.info(f"The output info is saved in {file_name}")
        # get min index
        min_index = np.argsort(output_list[:, 1])[0]
        self.logger.info(
            f"The min index is {min_index}, and latency is {output_list[min_index, 1]}"
        )

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
