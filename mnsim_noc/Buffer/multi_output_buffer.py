#-*-coding:utf-8-*-
"""
@FileName:
    multi_output_buffer.py
@Description:
    multi output buffer for multi output
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 19:53
"""
from mnsim_noc.utils.component import Component
from mnsim_noc.Buffer.output_buffer import OutputBuffer

class MultiOutputBuffer(Component):
    """
    multi output buffer
    """
    REGISTRY = "multi_buffer"
    NAME = "behavior_buffer_output"
    def __init__(self, buffer_size, output_target_id):
        super(MultiOutputBuffer, self).__init__()
        # init multi output buffer, id with target
        self.output_target_id = output_target_id
        self.output_buffer_list = dict()
        for target_tile_id in self.output_target_id:
            self.output_buffer_list[str(target_tile_id)] = \
                OutputBuffer(buffer_size)
        # assert output target id
        assert len(output_target_id) > 0, "output target id is empty"
        if len(output_target_id) == 1 and output_target_id[0] == -1:
            self.set_end()

    def check_enough_space(self, data_list):
        """
        check if the buffer has enough space to add the data
        """
        enough = [output_buffer.check_enough_space(data_list)
            for output_buffer in self.output_buffer_list.values()
        ]
        return all(enough)

    def add_data_list(self, data_list):
        """
        add data list to the buffer
        """
        for output_buffer in self.output_buffer_list.values():
            output_buffer.add_data_list(data_list)

    def next_transfer_data(self, target_tile_id):
        """
        get the next transfer data of the target tile id
        """
        return self.output_buffer_list[str(target_tile_id)].next_transfer_data()

    def delete_data_list(self, data_list, target_tile_id):
        """
        delete data list from the buffer
        """
        return self.output_buffer_list[str(target_tile_id)].delete_data_list(data_list)

    def set_end(self):
        """
        set end flag
        """
        for output_buffer in self.output_buffer_list.values():
            output_buffer.set_end()

    def check_finish(self):
        """
        check if the buffer is finished
        """
        for output_buffer in self.output_buffer_list.values():
            output_buffer.check_finish()
