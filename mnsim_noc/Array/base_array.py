#-*-coding:utf-8-*-
"""
@FileName:
    base_time_slice_array.py
@Description:
    Base Array class
@CreateTime:
    2021/10/08 18:21
"""
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
        # show the computation andcommunication range on each task and each image
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

    def show_simulation_result(self):
        """
        show the simulation result
        """
        self.show_latency_throughput()
        # show the tile result
        end_time = self.time_point_list[-1]
        tile_load_rate = [tile.get_simulation_result(end_time) for tile in self.tile_list]
        communication_load_rate = [
            communication.get_simulation_result(end_time)
            for communication in self.communication_list
        ]
        # inline function
        def _get_str(load_rate):
            return " ".join([f"{x:.3f}" for x in load_rate]) + \
                f", max is {max(load_rate):.4f}"
        self.logger.info(f"Total computation time is {end_time/1e6:.3f} ms")
        # print("For the tile")
        # print(_get_str(tile_load_rate))
        # print("For the communication")
        # print(_get_str(communication_load_rate))
        return tile_load_rate, communication_load_rate
