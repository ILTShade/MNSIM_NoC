# -*-coding:utf-8-*-
"""
@FileName:
    fc_time_slice_tile.py
@Description:
    Fully Connected Tile class for time slice
@CreateTime:
    2021/11/1 21:00
"""
from mnsim_noc.Tile import TimeSliceTile


class FCTimeSliceTile(TimeSliceTile):
    NAME = "fc_time_slice_tile"

    def __init__(self, position, task_cfg):
        # input and output data
        # format: (start_tile_id, end_tile_id, layer, x, y, length)
        """
        task_cfg properties:
            length:
                length of output data
            layer_in:
                Input layer num
            layer_out:
                Output layer num
            num_in:
                Number of inputs required for a node in input feature map
            num_out:
                Number of outputs required for a node in output feature map
            height_input; width_input:
                height and width of the input feature
            height_output; width_output:
                height and width of the output feature
            computing_time:
                Number of time slice required for computing a node on output feature
            end_tiles:
                List of id of tiles where the outputs should be sent to
            aggregate:
                whether the tile is a merging node or not
        """
        super().__init__(self, position, task_cfg)
        # Coordinate of the output under computation on the output feature map
        self.input_complete = False
        self.output_complete = False

    def update_time_slice(self):
        # Computing process in fc tile
        # if the tile finishes computing
        if self.output_complete:
            return
        # if the tile is not computing
        if self.state == 0:
            # if the input satisfy the requirement
            if self.latest_input == (self.height_input, self.width_input):
                self.state = self.computing_time
                self.input_complete = True
        # compute in the time slice
        if self.state > 0:
            self.state -= 1
        # if the tile just finished the computation
        if self.state == 0:
            if self.input_complete:
                for i in range(1, self.height_output):
                    for j in range(1, self.width_input):
                        if self.num_out == 1:
                            self.output_list.append((i, j))
                        elif (i, j) in self.output_to_be_merged:
                            current_num = self.output_to_be_merged[(i, j)]
                            if current_num == self.num_out - 1:
                                self.output_list.append((i, j))
                                del self.output_to_be_merged[(i, j)]
                            else:
                                self.output_to_be_merged[(i, j)] = current_num + 1
                        # if not
                        else:
                            self.output_to_be_merged[(i, j)] = 1
                # delete all inputs
                self.input_list = []
                self.output_complete = True
