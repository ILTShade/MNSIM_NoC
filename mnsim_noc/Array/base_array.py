#-*-coding:utf-8-*-
"""
@FileName:
    base_time_slice_array.py
@Description:
    Base Array class
@CreateTime:
    2021/10/08 18:21
"""
from bdb import effective
import time
import pandas as pd
import os
import random
import string
from mnsim_noc.utils.component import Component
from mnsim_noc.Strategy.mapping import Mapping
from mnsim_noc.Strategy.schedule import Schedule
from mnsim_noc.Wire.wire_net import _get_map_key


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
        # self.output_behavior_list = self.mapping_strategy.mapping_net()[0]
        # self.output_behavior_list_cp = self.mapping_strategy.mapping_net()[1]
        self.output_behavior_list, self.output_behavior_list_cp = self.mapping_strategy.mapping_net()
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

        # record the latency
        self.latency_list = []
        # record the equivalent communication amount
        self.r_communication_list = []
        self.e_communication_list = []
        # info for csv
        self.csv_info = '-'.join([str(mapping_strategy), str(schedule_strategy), str(image_num)])

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

    def run_single(self, tile_list, communication_list, wire_net):
        """
        run the simulation for single pass
        """
        schedule_strategy = Schedule.get_class_(self.schedule_strategy)(
            communication_list, wire_net
        )
        # init current time and time point list
        current_time = 0.
        time_point_list = []
        update_module = self.mapping_strategy.get_update_order(
            tile_list, communication_list
        )
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
        # check if the simulation is over
        self.check_finish(tile_list, communication_list, wire_net)
        return time_point_list

    def _get_e_communication(self, communication_list):
        """
        get the equivalent communication amount
        """
        # compute the equivalent communication amount
        occupy_list = []
        amount_list = []
        path_list = []
        layer_list = []
        for communication in communication_list:
            occupy_list.append(communication.get_communication_range())
            amount_list.append(communication.get_communication_amount())
            path_list.append([_get_map_key(path) for path in communication.get_path()])
            layer_list.append(communication.get_layer_info())

        # compute the conflict rate
        communication_len = len(communication_list)
        conflict_matrix = [[0]*communication_len for _ in range(0,communication_len)]
        effective_communication_list = [[0]*communication_len]
        for i in range(communication_len):
            # get self occupy time
            self_occupy_time = sum(map(lambda x: x[1]-x[0], occupy_list[i]))
            # get ratio
            for j in range(communication_len):
                if i == j:
                    continue
                if len(set(path_list[i]) & set(path_list[j])) == 0:
                    continue
                common_time = 0.
                range_i, range_j = 0, 0
                while True:
                    common_time += max(0,
                        min(occupy_list[i][range_i][1], occupy_list[j][range_j][1]) - \
                        max(occupy_list[i][range_i][0], occupy_list[j][range_j][0])
                    )
                    # append range_i or range_j
                    if occupy_list[i][range_i][1] <= occupy_list[j][range_j][0]:
                        range_i += 1
                        if range_i >= len(occupy_list[i]):
                            break
                    else:
                        range_j += 1
                        if range_j >= len(occupy_list[j]):
                            break
                conflict_matrix[i][j] = common_time / self_occupy_time
        
        # compute the equivalent communication amount
        r_amount = 0.
        e_amount = 0.
        # compute for each communication
        effective_communication_list = [[0]*communication_len]
        for i in range(communication_len):
            tmp = amount_list[i] * len(path_list[i])
            e_tmp = tmp
            r_amount += tmp
            for j in range(communication_len):
                # e_tmp = e_tmp / (1 - 0.5*conflict_matrix[i][j])   # repeated divide
                e_tmp = max(e_tmp, tmp/(1 - 0.5*conflict_matrix[i][j])) # maximum divide
            effective_communication_list[i] = e_tmp
        # compute for each layer
        layer_dict = {}
        for i in range(communication_len):
            if layer_list[i][0] in layer_dict.keys():
                layer_dict[layer_list[i][0]] = max(layer_dict[layer_list[i][0]], effective_communication_list[i])
            else:
                layer_dict[layer_list[i][0]] = effective_communication_list[i]
        # sum all layer
        for _,value in layer_dict.items():
            e_amount += value
        # return results
        return r_amount, e_amount

    def run(self):
        """
        run the array
        """
        for _, (fitness, tile_list, communication_list, wire_net) in \
            enumerate(self.output_behavior_list):
            # init wire net and schedule
            wire_net.set_transparent_flag(False)
            time_point_list = self.run_single(tile_list, communication_list, wire_net)
            # log info
            self.logger.info(f"Origin, for the {_}th: {fitness}, {time_point_list[-1]/1e6:.3f}")
            self.latency_list.append(time_point_list[-1])

        for _, (fitness, tile_list, communication_list, wire_net) in \
            enumerate(self.output_behavior_list_cp):
            # init wire net and schedule
            wire_net.set_transparent_flag(True)
            time_point_list = self.run_single(tile_list, communication_list, wire_net)
            self.logger.info(f"Transparent, for the {_}th: {fitness}, {time_point_list[-1]/1e6:.3f}")
            r_amount, e_amount = self._get_e_communication(communication_list)
            self.r_communication_list.append(r_amount)
            self.e_communication_list.append(e_amount)
            # draw / log
        dataframe = pd.DataFrame({
            "通信总量": self.r_communication_list,
            "等效通信总量": self.e_communication_list,
            "延时": self.latency_list
        })
        random.seed(time.time())
        for i in range(1000):
            filename = self.csv_info + f'-{time.localtime().tm_mon}-{time.localtime().tm_mday}-({time.localtime().tm_hour}-{time.localtime().tm_min}-{time.localtime().tm_sec})-{random.randint(0,100000)}.csv'
            if not os.path.exists(filename):
                dataframe.to_csv(filename, index=False, sep=',')
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
