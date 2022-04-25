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

    def __init__(self, position, task_cfg, time_slice, quiet):
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
        super().__init__(position, task_cfg, time_slice, quiet)
        # Extract parameters from task_cfg
        self.height_filter = task_cfg['height_filter']
        self.width_filter = task_cfg['width_filter']
        self.stride_filter = task_cfg['stride_filter']
        self.padding_filter = task_cfg['padding_filter']
        # Coordinate of the output under computation on the output feature map
        self.computing_output = None
        # Coordinate of the output to be computed next on the output feature map
        self.next_output = (1, 1, 0)
        # Coordinate of the bottom right corner of the useless input
        # format: (x, y, h)
        self.useless = (0, 0, 0)

    def set_tile_task(self, clock_num):
        # if the tile was not computing
        if self.state == 0:
            # allocate computation task
            if self.input_list:
                # if input of the image is over
                if self.input_count == self.height_input * self.width_input:
                    self.input_image_id += 1
                    self.input_count = 0
                # solve the required data
                x_max = self.height_filter + self.stride_filter * (self.next_output[0] - 1) - self.padding_filter
                x_req = min(self.height_input,x_max)
                y_max = self.width_filter + self.stride_filter * (self.next_output[1] - 1) - self.padding_filter
                y_req = min(self.width_input,y_max)
                # if the input_list satisfy the requirement for next output, then allocate the computation task
                satisfy = True
                for x in range(0,self.height_filter):
                    for y in range(0,self.width_filter):
                        # padding nodes not included
                        if 1 <= x_max-x <= self.height_input and 1 <= y_max-y <= self.width_input:
                            if (x_max-x,y_max-y,self.output_image_id) not in self.input_list:
                                satisfy = False
                                break
                    if not satisfy:
                        break
                if satisfy:
                    if self.output_cache_size >= (len(self.output_list) + 1) * self.data_length:
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
                        if not self.quiet:
                            self.logger.info('(Compute) image_id:'+str(self.output_image_id)+' layer:'+str(self.layer_out)+' start:'+str(clock_num*self.time_slice)+' finish:'+str((clock_num+self.computing_time)*self.time_slice)+' tile_id:'+str(self.tile_id)+' data:'+str(self.computing_output)+str(self.useless))
                        # update self.next_output
                        x_new = (self.next_output[0] * self.width_output + self.next_output[1]) // self.width_output
                        y_new = (self.next_output[0] * self.width_output + self.next_output[1]) % self.width_output + 1
                        if x_new > self.height_output:
                            self.next_output = (1, 1, self.output_image_id+1)
                        else:
                            self.next_output = (x_new, y_new, self.output_image_id)
                        # update state
                        self.state = self.computing_time
                    else:
                        if not self.quiet:
                            self.logger.info('(Output cache occupied) image_id:'+str(self.output_image_id)+' layer:'+str(self.layer_out)+' start:'+str(clock_num*self.time_slice)+' finish:'+str((clock_num+self.computing_time)*self.time_slice)+' tile_id:'+str(self.tile_id)+' data:'+str(self.computing_output)+str(self.useless))


    def update_time_slice(self, n):
        # Computing process in pooling tile
        # compute in the time slice
        if self.state > 0:
            self.state -= n
        # if self.state < 0:
        #     self.logger.warn('tile state < 0')
        #     exit()
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
                # delete useless inputs from input_list considering the self.useless
                list_for_search = self.input_list[:]
                for single_input in list_for_search:
                    if single_input[2] == self.output_image_id:
                        if single_input[0] <= self.useless[0] - self.useless[2] or (
                                single_input[0] <= self.useless[0] and single_input[1] <= self.useless[1]):
                            self.input_list.remove(single_input)
                # update the output image id
                if self.computing_output[0] == self.height_output and self.computing_output[1] == self.width_output:
                    self.output_image_id += 1
                # delete the computing output
                self.computing_output = None
