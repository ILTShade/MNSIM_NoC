# -*-coding:utf-8-*-
"""
@FileName:
    base_tile.py
@Description:
    Base Tile class for time slice
@CreateTime:
    2021/10/08 17:57
"""
import copy
from mnsim_noc.utils.component import Component
from mnsim_noc.Buffer import InputBuffer, MultiOutputBuffer

class BaseTile(Component):
    """
    Base Tile class for behavior-driven simulation
    position: tuple -> (row, column)
    tile_behavior_cfg: dict (key, value):
        task_id, layer_id, tile_id, target_tile_id, and dependence
        dependence is a list, each item is a dict
            wait, output, drop, and latency
    """
    REGISTRY = "tile"
    NAME = "behavior_driven"
    def __init__(self, position, image_num, buffer_size, tile_behavior_cfg):
        """
        image_num: int, throughput
        buffer_size: tuple of int, (buffer_size_input, buffer_size_output), bits
        """
        super(BaseTile, self).__init__()
        # position and tile_behavior_cfg
        self.position = position
        self.image_num = image_num
        self.tile_behavior_cfg = copy.deepcopy(tile_behavior_cfg)
        # other parameters
        self.task_id = tile_behavior_cfg["task_id"] # value
        self.tile_id = tile_behavior_cfg["tile_id"] # value
        self.layer_id = tile_behavior_cfg["layer_id"] # value
        self.target_tile_id = tile_behavior_cfg["target_tile_id"] # this is a list
        self.merge_flag = tile_behavior_cfg.get("merge_flag", False)
        # input buffer and output buffer
        self.input_buffer = InputBuffer(buffer_size[0])
        self.output_buffer = MultiOutputBuffer(buffer_size[1], self.target_tile_id)
        # running state, False for idle, True for running
        self.running_state = False
        self.computation_list = self._get_computation_list()
        self.computation_id = 0
        self.computation_end_time = float("inf")
        self.computation_range_time = []

    def _get_computation_list(self):
        """
        get the computation list
        each item is a tuple, (dependence, done_flag)
        done_flag, idle, running, done
        """
        computation_list = []
        dependence_length = len(self.tile_behavior_cfg["dependence"])
        for i in range(self.image_num):
            for j in range(dependence_length):
                dependence = copy.deepcopy(self.tile_behavior_cfg["dependence"][j])
                # modify dependence base on image num
                for key in ["wait", "output", "drop"]:
                    for value in dependence[key]:
                        # x, y, start, end, bit, total, image_id, layer_id, tile_id
                        value[6] = i
                computation_list.append([dependence, "idle"])
        return computation_list

    def update(self, current_time):
        """
        suppose the time reaches current_time
        for different running state, update the tile
        ONLY update function can change the running_state
        """
        # first for the running state, can change to idle
        if self.running_state:
            if current_time >= self.computation_end_time:
                # get computation
                computation = self.computation_list[self.computation_id][0]
                # modify state
                self.running_state = False
                self.computation_list[self.computation_id][1] = "done"
                self.computation_id += 1
                # modify buffer
                self.input_buffer.delete_data_list(computation["drop"])
                self.output_buffer.add_data_list(computation["output"])
            else:
                return None
        assert self.running_state == False, "running_state should be idle"
        if self.computation_id >= len(self.computation_list):
            # if all computation are done, return None
            return None
        computation = self.computation_list[self.computation_id][0]
        # for idle state, running state is False
        # check if the computation can run
        if self.input_buffer.check_data_already(computation["wait"]) \
            and self.output_buffer.check_enough_space(computation["output"]):
            self.running_state = True
            self.computation_list[self.computation_id][1] = "running"
            assert computation["latency"] > 0, "latency should be positive"
            self.computation_end_time = current_time + computation["latency"]
            self.computation_range_time.append((current_time, self.computation_end_time))
            return None
        else:
            self.computation_end_time = float("inf")

    def get_computation_end_time(self):
        """
        get the end time of the computation
        """
        if self.running_state:
            return self.computation_end_time
        else:
            return float("inf")

    def get_computation_range(self):
        """
        get the range of the computation
        """
        computation_range = []
        dependence_length = len(self.tile_behavior_cfg["dependence"])
        for i in range(self.image_num):
            computation_range.append([])
            for j in range(dependence_length):
                computation_range[-1].append(self.computation_range_time[i*dependence_length+j])
        return computation_range
