#-*-coding:utf-8-*-
"""
@FileName:
    base_time_slice_array.py
@Description:
    Base Array class
@CreateTime:
    2021/10/08 18:21
"""
import os
import time
import numpy as np
import random
from mnsim_noc.utils.component import Component
from mnsim_noc.Strategy.mapping import Mapping
from mnsim_noc.Strategy.schedule import Schedule

class BaseArray(Component):
    """
    base array for behavior driven simulation
    """
    REGISTRY = "array"
    NAME = "behavior_driven"
    def __init__(self, task_behavior_list, image_num,
        tile_net_shape, buffer_size, band_width,
        mapping_strategy="naive", schedule_strategy="naive", transparent_flag=False
    ):
        super(BaseArray, self).__init__()
        # logging
        self.logger.info("Initializing the array")
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
            task_behavior_list, image_num, tile_net_shape, buffer_size, band_width
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
        behavior_number = []
        for _, task_behavior in enumerate(task_behavior_list):
            # for tile number
            tile_number.append(len(task_behavior))
            # for the communication number and behavior number
            task_communication_number = 0
            task_behavior_number = 0
            for tile_behavior in task_behavior:
                repeated_number = 1
                if tile_behavior["target_tile_id"] != [-1]:
                    task_communication_number += len(tile_behavior["target_tile_id"])
                    repeated_number += len(tile_behavior["target_tile_id"])
                task_behavior_number += len(tile_behavior["dependence"]) * repeated_number
            communication_number.append(task_communication_number)
            behavior_number.append(task_behavior_number)
        # logger
        self.logger.info(
            f"In total, {sum(tile_number)} tiles," + \
            f" {sum(communication_number)} communications," + \
            f" {sum(behavior_number)} behaviors"
        )
        for i in range(len(task_behavior_list)):
            self.logger.info(
                f"\tTask {i} has {tile_number[i]} tiles," + \
                f" {communication_number[i]} communications," + \
                f" {behavior_number[i]} behaviors"
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
            # save for the output
        output_list = np.array(output_list)
        while True:
            file_name = f"output_info_{random.randint(1, 99):02d}.txt"
            if os.path.exists(file_name):
                continue
            np.savetxt(file_name, output_list, fmt="%.3f")
            self.logger.info(f"The output info is saved in {file_name}")
            break

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
