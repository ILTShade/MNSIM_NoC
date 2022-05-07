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
    ):
        super(BaseArray, self).__init__()
        self.mapping_strategy = Mapping(
            task_behavior_list, image_num,  tile_net_shape, buffer_size, band_width
        )
        self.tile_list, self.communication_list = self.mapping_strategy.mapping_net()
        self.schedule_strategy = Schedule(self.tile_list, self.communication_list)

    def run(self):
        """
        run the array
        """
        current_time = 0
        update_module = self.mapping_strategy.get_update_order(
            self.tile_list, self.communication_list
        )
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
