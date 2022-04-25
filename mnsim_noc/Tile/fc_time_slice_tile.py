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

    def __init__(self, position, task_cfg, time_slice, quiet):
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
        """
        super().__init__(position, task_cfg, time_slice, quiet)
        # Coordinate of the output under computation on the output feature map
        self.computing_output = False
        self.output_complete = False

    def set_tile_task(self, clock_num):
        # if the tile is not computing
        if self.state == 0:
            # if the input_list satisfy the requirement for next output, then allocate the computation task
            if self.input_count == self.height_input:
                self.state = self.computing_time
                self.computing_output = True
                # update the received image id
                # TODO: 考虑流水线输入的总图片数量
                self.input_image_id += 1
                self.input_count = 0
                # log the computing time(ns)
                if not self.quiet:
                    self.logger.info('(Compute) image_id:'+str(self.output_image_id)+' layer:'+str(self.layer_out)+' start:'+str(clock_num*self.time_slice)+' finish:'+str((clock_num+self.computing_time)*self.time_slice)+' tile_id:'+str(self.tile_id))

    def update_time_slice(self, n):
        # Computing process in fc tile
        # compute in the time slice
        if self.state > 0:
            self.state -= n
        # if the tile just finished the computation
        if self.state == 0:
            if self.computing_output:
                for i in range(1, self.height_output+1):
                    self.computed_data += self.data_length
                    if self.num_out == 1:
                        self.output_list.append((i, -1))
                    elif (i, -1) in self.output_to_be_merged:
                        current_num = self.output_to_be_merged[(i, -1)]
                        if current_num == self.num_out - 1:
                            self.output_list.append((i, -1))
                            del self.output_to_be_merged[(i, -1)]
                        else:
                            self.output_to_be_merged[(i, -1)] = current_num + 1
                    # if not
                    else:
                        self.output_to_be_merged[(i, -1)] = 1
                # delete all inputs from the current image id
                for input in self.input_list[:]:
                    if input[2] == self.output_image_id:
                        self.input_list.remove(input)
                # update the computing image_id
                self.output_image_id += 1
                self.computing_output = False
