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
        mapping_strategy="naive", schedule_strategy="naive"
    ):
        super(BaseArray, self).__init__()
        self.mapping_strategy = Mapping.get_class_(mapping_strategy)(
            task_behavior_list, image_num, tile_net_shape, buffer_size, band_width
        )
        self.tile_list, self.communication_list, self.wire_net = self.mapping_strategy.mapping_net()
        self.schedule_strategy = Schedule.get_class_(schedule_strategy)(
            self.communication_list, self.wire_net
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
        print("Total time: {} ns".format(end_time))
        print("For the tile")
        print(_get_str(tile_load_rate))
        print("For the communication")
        print(_get_str(communication_load_rate))
