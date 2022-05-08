#-*-coding:utf-8-*-
"""
@FileName:
    input_buffer.py
@Description:
    input behavior buffer
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 10:15
"""
from mnsim_noc.Buffer.base_buffer import BaseBuffer, get_data_size

class InputBuffer(BaseBuffer):
    """
    input behavior buffer
    """
    NAME = "behavior_buffer_input"
    def __init__(self, buffer_size):
        super(InputBuffer, self).__init__(buffer_size)
        # for input buffer, there may be transfer data to add
        self.transfer_data = []
        self.transfer_data_size = 0
        # cache for check already
        self.cache = {}
        self.start_flag = False

    def check_remain_size(self):
        """
        check the remain size, considering the transfer data
        """
        return self.buffer_size - self.used_space - self.transfer_data_size

    def check_enough_space(self, data_list):
        """
        check if the buffer has enough space to add the data
        """
        data_size = sum([get_data_size(data) for data in data_list])
        return self.check_remain_size() >= data_size

    def _add_transfer_one(self, data):
        """
        add one data to the transfer data
        """
        self.transfer_data.append(data)
        self.transfer_data_size += get_data_size(data)

    def add_transfer_data_list(self, data_list):
        """
        add list data to the transfer data
        """
        for data in data_list:
            self._add_transfer_one(data)

    def _delete_transfer_one(self, data):
        """
        delete one data in the transfer data
        """
        self.transfer_data.remove(data)
        self.transfer_data_size -= get_data_size(data)

    def delete_transfer_data_list(self, data_list):
        """
        delete list data from the transfer data
        """
        for data in data_list:
            self._delete_transfer_one(data)

    def add_data_list(self, data_list):
        """
        add list data to the buffer
        """
        assert not self.start_flag, "the input buffer is already started"
        # the data must come from transfer data
        self.delete_transfer_data_list(data_list)
        # add data list
        super(InputBuffer, self).add_data_list(data_list)
        # clear the cache
        self.cache.clear()

    def check_data_already(self, data_list):
        """
        check if the data is already in the buffer
        """
        if self.start_flag:
            return True
        key = str(data_list)
        if key in self.cache:
            return self.cache[key]
        else:
            # check the data already
            value = all([data in self.buffer_data for data in data_list])
            self.cache[key] = value
            return value

    def delete_data_list(self, data_list):
        """
        delete list data from the buffer
        """
        if not self.start_flag:
            super(InputBuffer, self).delete_data_list(data_list)
            self.cache.clear()

    def set_start(self):
        """
        set this input buffer to the start
        """
        self.start_flag = True
