# -*-coding:utf-8-*-
"""
@FileName:
    pooling_time_slice_tile.py
@Description:
    Pooling Tile class for time slice
@CreateTime:
    2021/11/3 19:30
"""
from mnsim_noc.Tile import TimeSliceTile


class PoolingTimeSliceTile(TimeSliceTile):
    NAME = "pooling_time_slice_tile"

    def __init__(self, position, task_cfg, time_slice):
        # input and output data
        # format: (start_tile_id, end_tile_id, layer, x, y, length)
        """
        task_cfg properties:
            length:
                length of output data
            layer_in:
                Input layer
            layer_out:
                Output layer
            num_out:
                Number of outputs required for a node in output feature map
            height_filter; width_filter; stride_filter; padding_filter:
                Parameter of the convolution kernel
            height_input; width_input:
                height and width of the input feature
            height_output; width_output:
                height and width of the output feature
            computing_time:
                Number of time slice required for computing a node on output feature
            end_tiles:
                List of id of tiles where the outputs should be sent to
        """
        super().__init__(position, task_cfg, time_slice)
        # Extract parameters from task_cfg
        self.height_filter = task_cfg['height_filter']
        self.width_filter = task_cfg['width_filter']
        self.stride_filter = task_cfg['stride_filter']
        self.padding_filter = task_cfg['padding_filter']
        # Coordinate of the output under computation on the output feature map
        self.computing_output = None
        # Coordinate of the output to be computed next on the output feature map
        self.next_output = (1, 1)
        # Coordinate of the bottom right corner of the useless input
        # format: (x, y, h)
        self.useless = (0, 0, 0)

    def set_tile_task(self, clock_num):
        # if the tile was not computing
        if self.state == 0:
            # allocate computation task
            if self.input_list:
                x_req = min(self.height_input,
                            self.height_filter + self.stride_filter * (self.next_output[0] - 1) - self.padding_filter)
                y_req = min(self.width_input,
                            self.width_filter + self.stride_filter * (self.next_output[1] - 1) - self.padding_filter)
                # if the input_list satisfy the requirement for next output, then allocate the computation task
                if (self.latest_input[0] * self.width_input + self.latest_input[1]) >= (
                        x_req * self.width_input + y_req):
                    # update self.useless
                    if self.height_filter + self.stride_filter * (self.next_output[0] - 1) - self.padding_filter == self.height_input + self.padding_filter:
                        x_useless = x_req
                        h_useless = self.height_filter - self.padding_filter
                    else:
                        x_useless = min(x_req - self.height_filter + self.stride_filter, self.height_input)
                        h_useless = self.stride_filter
                    if self.width_filter + self.stride_filter * (self.next_output[1] - 1) - self.padding_filter == self.width_input + self.padding_filter:
                        y_useless = y_req
                    else:
                        y_useless = min(y_req - self.width_filter + self.stride_filter, self.width_input)
                    self.useless = (x_useless, y_useless, h_useless)
                    # update self.computing_output
                    self.computing_output = self.next_output
                    # log the computing time(ns)
                    self.logger.info('(Compute) layer:'+str(self.layer_out)+' start:'+str(clock_num*self.time_slice)+' finish:'+str((clock_num+self.computing_time)*self.time_slice)+' tile_id:'+str(self.tile_id))
                    # update self.next_output
                    x_new = (self.next_output[0] * self.width_output + self.next_output[1]) // self.width_output
                    y_new = (self.next_output[0] * self.width_output + self.next_output[1]) % self.width_output + 1
                    self.next_output = (x_new, y_new)
                    # update state
                    self.state = self.computing_time

    def update_time_slice(self, n):
        # Computing process in pooling tile
        # compute in the time slice
        if self.state > 0:
            self.state -= n
        # if the tile just finished the computation
        if self.state == 0:
            if self.computing_output:
                self.computed_data += self.data_length
                if self.num_out == 1:
                    self.output_list.append(self.computing_output)
                elif self.computing_output in self.output_to_be_merged:
                    current_num = self.output_to_be_merged[self.computing_output]
                    if current_num == self.num_out - 1:
                        self.output_list.append(self.computing_output)
                        del self.output_to_be_merged[self.computing_output]
                    else:
                        self.output_to_be_merged[self.computing_output] = current_num + 1
                # if not
                else:
                    self.output_to_be_merged[self.computing_output] = 1
                self.computing_output = None
                # delete useless inputs from input_list considering the self.useless
                list_for_search = self.input_list[:]
                for single_input in list_for_search:
                    if single_input[0] <= self.useless[0] - self.useless[2] or (
                            single_input[0] <= self.useless[0] and single_input[1] <= self.useless[1]):
                        self.input_list.remove(single_input)
