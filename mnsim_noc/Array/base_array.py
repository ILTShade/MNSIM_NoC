#-*-coding:utf-8-*-
"""
@FileName:
    base_time_slice_array.py
@Description:
    Base Array class
@CreateTime:
    2021/10/08 18:21
"""
import numpy as np
import pickle
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
            f"\tStartegy are {mapping_strategy}, {schedule_strategy}, {transparent_flag}"
        )
        # show the array
        self._get_behavior_number(task_behavior_list)
        # init
        self.mapping_strategy = Mapping.get_class_(mapping_strategy)(
            task_behavior_list, image_num, tile_net_shape, buffer_size, band_width
        )
        self.tile_list, self.communication_list, self.wire_net = self.mapping_strategy.mapping_net()
        # set transparent
        self.wire_net.set_transparent_flag(transparent_flag)
        self.schedule_strategy = Schedule.get_class_(schedule_strategy)(
            self.communication_list, self.wire_net
        )
        # time point list
        self.image_num = image_num
        self.tile_net_shape = tile_net_shape
        self.time_point_list = []

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
        current_time = 0.
        update_module = self.mapping_strategy.get_update_order(
            self.tile_list, self.communication_list
        )
        self.time_point_list = []
        while True:
            # running the data
            for module in update_module:
                module.update(current_time)
            # schedule for the path
            self.schedule_strategy.schedule(current_time)
            # get next time
            next_time = min([
                min([tile.get_computation_end_time() for tile in self.tile_list]),
                min([
                    communication.get_communication_end_time()
                    for communication in self.communication_list
                ])
            ])
            # check if the simulation is over
            assert next_time > current_time
            current_time = next_time
            if current_time == float("inf"):
                break
            self.time_point_list.append(current_time)
        # check if the simulation is over
        self.check_finish()

    def check_finish(self):
        """
        check if the simulation is over and right
        """
        # check if the tile is finished
        for tile in self.tile_list:
            tile.check_finish()
        # check if the communication is finished
        for communication in self.communication_list:
            communication.check_finish()
        # check if the wire net is finished
        self.wire_net.check_finish()

    def show_latency_throughput(self):
        """
        show the latency and throughput
        """
        # show the computation and communication range on each task and each image
        complete_time = {} # each task, and list for each image
        for tile in self.tile_list:
            task_id = tile.task_id
            if task_id not in complete_time:
                complete_time[task_id] = \
                    [[float("inf"), float("-inf")] for _ in range(self.image_num)]
            computation_range = tile.get_computation_range()
            assert len(computation_range) == self.image_num
            for i in range(self.image_num):
                complete_time[task_id][i][0] = min([
                    complete_time[task_id][i][0], computation_range[i][0][0]
                ])
                complete_time[task_id][i][1] = max([
                    complete_time[task_id][i][1], computation_range[i][-1][1]
                ])
        # logger complete time
        for task_id, computation_range in complete_time.items():
            al = sum([x[1]-x[0] for x in computation_range])/self.image_num
            output_str = f"Task {task_id} average latency is {al/1e6:.3f} ms"
            if self.image_num > 1:
                at = sum([
                    computation_range[i+1][1]-computation_range[i][1]
                    for i in range(self.image_num-1)
                ])/(self.image_num-1)
                output_str += f", average throughput is {at/1e6:.3f} ms"
            else:
                output_str += ", no throughput time"
            output_str += f", total cost time is " + \
                f"{(computation_range[-1][1]-computation_range[0][0])/1e6:.3f} ms"
            self.logger.info(output_str)
            for i, sl in enumerate(computation_range):
                self.logger.info(
                    f"\tImage {i} range is {sl[0]/1e6:.3f} ms to {sl[1]/1e6:.3f} ms"
                )
        return complete_time

    def show_tile_wire_rate(self):
        """
        show the tile and wire running rate
        """
        # show the tile and wire running rate
        end_time = self.time_point_list[-1]
        tile_task_id = np.zeros(self.tile_net_shape, dtype=np.int)
        tile_load_rate = np.zeros(self.tile_net_shape)
        for tile in self.tile_list:
            position = tile.position
            tile_task_id[position] = tile.task_id + 1 # start from 1
            tile_load_rate[position] = tile.get_running_rate(end_time)
        horizontal_rate, vertical_rate = self.wire_net.get_running_rate(end_time)
        # get show tile row and show tile column
        show_tile_row = max([tile.position[0] for tile in self.tile_list]) + 1
        show_tile_column = max([tile.position[1] for tile in self.tile_list]) + 1
        # logger
        self.logger.info("For the tile")
        for i in range(show_tile_row):
            self.logger.info("-".join([
                f"{tile_task_id[i,j]},{tile_load_rate[i,j]:.3f}" \
                for j in range(show_tile_column)
            ]))
            if i != show_tile_row-1:
                self.logger.info(" ".join([
                    "   |   " for _ in range(show_tile_column)
                ]))
        # logger
        self.logger.info("For the wire")
        for i in range(show_tile_row):
            row_str = ""
            for j in range(show_tile_column - 1):
                row_str += f"{tile_task_id[i,j]}-{horizontal_rate[i,j]:.3f}-"
            self.logger.info(row_str + f"{tile_task_id[i, show_tile_column-1]}")
            # vertical
            split_str = "   ".join(["|    " for _ in range(show_tile_column)])
            if i != show_tile_row-1:
                self.logger.info(split_str)
                self.logger.info("   ".join([
                    f"{vertical_rate[i,j]:.3f}" for _ in range(show_tile_column)
                ]))
                self.logger.info(split_str)
        return tile_task_id, tile_load_rate, horizontal_rate, vertical_rate

    def get_communication_wire_info(self):
        """
        get communication info and wire info, range
        """
        communication_info_list = []
        for communication in self.communication_list:
            communication_info_list.append({
                "start_tile": communication.input_tile.position,
                "end_tile": communication.output_tile.position,
                "range": communication.get_communication_range(),
            })
        wire_info_list = self.wire_net.get_wire_range()
        # save file
        file_name = "tmp.pkl"
        with open(file_name, "wb") as f:
            pickle.dump(communication_info_list, f)
            pickle.dump(wire_info_list, f)

    def show_simulation_result(self):
        """
        show the simulation result
        """
        self.show_latency_throughput()
        # self.show_tile_wire_rate()
        self.get_communication_wire_info()
