#-*-coding:utf-8-*-
"""
@FileName:
    output_buffer.py
@Description:
    output behavior buffer of the Tile
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 10:51
"""
from mnsim_noc.Buffer.base_buffer import BaseBuffer, get_data_size

class OutputBuffer(BaseBuffer):
    """
    output behavior buffer
    """
    NAME = "behavior_buffer_output"
    def __init__(self, buffer_size):
        super(OutputBuffer, self).__init__(buffer_size)
        self.end_flag = False

    def check_remain_size(self):
        """
        check the remain size, for the computing
        """
        if self.end_flag:
            return float("inf")
        return self.buffer_size - self.used_space

    def check_enough_space(self, data_list):
        """
        check if the buffer has enough space to add the data
        """
        data_size = sum([get_data_size(data) for data in data_list])
        return self.check_remain_size() >= data_size

    def next_transfer_data(self):
        """
        get the next transfer data
        """
        if self.end_flag:
            return None
        if len(self.buffer_data) == 0:
            return None
        else:
            return [self.buffer_data[0]]

    def set_end(self):
        """
        set this buffer ad the end buffer
        """
        self.end_flag = True

    def check_finish(self):
        """
        check if the buffer is finished
        """
        if not self.end_flag:
            assert len(self.buffer_data) == 0, "the buffer is not empty"
