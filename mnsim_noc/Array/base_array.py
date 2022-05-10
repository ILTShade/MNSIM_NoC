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
    REGISTRY = "array"
    NAME = "behavior_driven"
    """
    base array for behavior driven simulation
    """
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
        self.logger.info(f"\tStartegy are {mapping_strategy}, {schedule_strategy}, {transparent_flag}")
        # init
        self.mapping_strategy = Mapping.get_class_(mapping_strategy)(
            task_behavior_list, image_num, tile_net_shape, buffer_size, band_width
        )
        self.tile_list, self.communication_list, self.wire_net = self.mapping_strategy.mapping_net()
        # show the array
        self.logger.info(f"There are {len(self.tile_list)} TILES and {len(self.communication_list)} COMMUNICATIONS")
        self._get_behavior_number(task_behavior_list)
        # set transparent
        self.wire_net.set_transparent_flag(transparent_flag)
        self.schedule_strategy = Schedule.get_class_(schedule_strategy)(
            self.communication_list, self.wire_net
        )

    def _get_behavior_number(self, task_behavior_list):
        """
        get the behavior number
        """
        behavior_number = []
        for i, task_behavior in enumerate(task_behavior_list):
            task_behavior_number = 0
            for tile_behavior in task_behavior:
                repeated_number = 1
                if tile_behavior["target_tile_id"] != [-1]:
                    repeated_number += len(tile_behavior["target_tile_id"])
                task_behavior_number += len(tile_behavior["dependence"]) * repeated_number
            behavior_number.append(task_behavior_number)
        # logger
        self.logger.info(f"\tThere are {sum(behavior_number)} behaviors in single image")

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
                min([communication.get_communication_end_time() for communication in self.communication_list])
            ])
            # check if the simulation is over
            assert next_time > current_time
            current_time = next_time
            if current_time == float("inf"):
                break
            else:
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

    def show_simulation_result(self):
        """
        show the simulation result
        """
        # show the tile result
        end_time = self.time_point_list[-1]
        tile_load_rate = [tile.get_simulation_result(end_time) for tile in self.tile_list]
        communication_load_rate = [
            communication.get_simulation_result(end_time) for communication in self.communication_list
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
