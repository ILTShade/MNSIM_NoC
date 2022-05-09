#-*-coding:utf-8-*-
"""
@FileName:
    multi_input_buffer.py
@Description:
    multi input buffer to support element sum and merge node
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/09 15:05
"""
from mnsim_noc.utils.component import Component
from mnsim_noc.Buffer.base_buffer import get_data_tile
from mnsim_noc.Buffer.input_buffer import InputBuffer

class MultiInputBuffer(Component):
    """
    multi input buffer to support element sum and merge node
    """
    REGISTRY = "multi_buffer"
    NAME = "behavior_buffer_input"
    def __init__(self, buffer_size, input_source_id):
        super(MultiInputBuffer, self).__init__()
        # init multi input buffer, id with source
        self.input_source_id = input_source_id
        self.input_buffer_dict = dict()
        for source_tile_id in self.input_source_id:
            self.input_buffer_dict[str(source_tile_id)] = \
                InputBuffer(buffer_size // len(self.input_source_id))
        # check
        self.start_flag = False
        assert len(input_source_id) > 0, "input source id is empty"
        if len(input_source_id) == 1 and input_source_id[0] == -1:
            self.set_start()

    def check_enough_space(self, data_list, source_tile_id):
        """
        check if the buffer has enough space to add the data
        """
        return self.input_buffer_dict[str(source_tile_id)].check_enough_space(data_list)

    def add_transfer_data_list(self, data_list, source_tile_id):
        """
        add data list to the buffer's transfer data
        """
        self.input_buffer_dict[str(source_tile_id)].add_transfer_data_list(data_list)

    def add_data_list(self, data_list, source_tile_id):
        """
        add data list to the buffer
        """
        self.input_buffer_dict[str(source_tile_id)].add_data_list(data_list)

    def _split_data_list(self, data_list):
        """
        split data list regarding the inuput_source_id
        """
        split_data_dict = dict()
        for data in data_list:
            source_tile_id = get_data_tile(data)
            split_data_dict[str(source_tile_id)] = \
                split_data_dict.get(str(source_tile_id), []) + [data]
        return split_data_dict

    def check_data_already(self, data_list):
        """
        check if the data is already in the buffer
        """
        if self.start_flag:
            return True
        split_data_dict = self._split_data_list(data_list)
        for k, v in split_data_dict.items():
            if not self.input_buffer_dict[k].check_data_already(v):
                return False
        return True

    def delete_data_list(self, data_list):
        """
        delete data list from the buffer
        """
        if self.start_flag:
            return None
        split_data_dict = self._split_data_list(data_list)
        for k, v in split_data_dict.items():
            self.input_buffer_dict[k].delete_data_list(v)

    def set_start(self):
        """
        set start flag
        """
        self.start_flag = True
        for _, v in self.input_buffer_dict.items():
            v.set_start()

    def check_finish(self):
        """
        check if the buffer is empty
        """
        for _, v in self.input_buffer_dict.items():
            v.check_finish()
