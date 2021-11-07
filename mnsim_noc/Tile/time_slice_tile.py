# -*-coding:utf-8-*-
"""
@FileName:
    time_slice_tile.py
@Description:
    Tile class for time slice
@CreateTime:
    2021/10/17 10:00
"""
from abc import abstractmethod
from mnsim_noc.Tile import BaseTile


class TimeSliceTile(BaseTile):
    NAME = "time_slice_tile"

    def __init__(self, position, task_cfg):
        super().__init__(self, position, task_cfg)
        # Extract parameters from task_cfg
        self.length = task_cfg.length
        self.layer_in = task_cfg.layer_in
        self.layer_out = task_cfg.layer_out
        self.num_in = task_cfg.num_in
        self.num_out = task_cfg.num_out
        self.height_input = task_cfg.height_input
        self.width_input = task_cfg.width_input
        self.height_output = task_cfg.height_output
        self.width_output = task_cfg.width_output
        self.computing_time = task_cfg.computing_time
        self.end_tiles = task_cfg.end_tiles
        # Number of inputs for a certain node in input feature map
        self.input_to_be_merged = dict()
        # Number of inputs for a certain node in input feature map
        self.output_to_be_merged = dict()
        # Coordinate of the latest input on the input feature map
        self.latest_input = (0, 0)
        # List of id of tiles where the current output still needs to be sent to
        self.current_end_tiles = self.end_tiles
        # whether the tile is transmitting data or not
        self.is_transmitting = False

    def update_input(self, inputs):
        # Update the input_list with new inputs
        # inputs format: (x, y, layer) on input feature map
        # Merge new inputs into nodes on input feature map, and then add to input_list
        for single_input in inputs:
            if single_input[2] == self.layer_in:
                if self.num_in == 1:
                    self.input_list.append(single_input[0:2])
                # if there exist inputs for the same node on input feature map
                elif single_input[0:2] in self.input_to_be_merged:
                    current_num = self.input_to_be_merged[single_input[0:2]]
                    if current_num == self.num_in - 1:
                        self.input_list.append(single_input[0:2])
                        self.latest_input = single_input[0:2]
                        del self.input_to_be_merged[single_input[0:2]]
                    else:
                        self.input_to_be_merged[single_input[0:2]] = current_num + 1
                # if not
                else:
                    self.input_to_be_merged[single_input] = 1
            elif single_input[2] == self.layer_out:
                if self.num_out == 1:
                    self.logger.warn("Error: wrong input layer")
                elif single_input[0:2] in self.output_to_be_merged:
                    current_num = self.output_to_be_merged[single_input[0:2]]
                    if current_num == self.num_out - 1:
                        self.output_list.append(single_input[0:2])
                        del self.output_to_be_merged[single_input[0:2]]
                    else:
                        self.output_to_be_merged[single_input[0:2]] = current_num + 1
                # if not
                else:
                    self.output_to_be_merged[single_input[0:2]] = 1

    @abstractmethod
    def update_time_slice(self):
        pass

    def update_output(self, outputs):
        # Update the output_list with outputs that have been transmitted through wires
        # outputs format: (x, y, end_tile_id)
        for single_output in outputs:
            if single_output[2] in self.current_end_tiles:
                self.current_end_tiles.remove(single_output[2])
            else:
                # TODO:log error
                pass
        if not self.current_end_tiles:
            self.output_list.pop()
            self.current_end_tiles = self.end_tiles
            self.is_transmitting = False

    def get_output(self):
        # return the output to be transmitted through wires
        # outputs format: (x, y, end_tile_id, length, layer_out)
        if self.output_list:
            output = self.output_list[0]
            return output[0], output[1], self.current_end_tiles[0], self.length, self.layer_out
