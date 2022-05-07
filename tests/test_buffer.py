#-*-coding:utf-8-*-
"""
@FileName:
    test_buffer.py
@Description:
    test buffer for input and output
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 11:09
"""
from mnsim_noc.Buffer import InputBuffer, OutputBuffer

def test_buffer():
    """
    test buffer of input and output
    """
    # buffer data example
    data_list = [
        [0, 0, 0, 3, 9, 3, 0, 0, -1],
        [0, 1, 0, 3, 9, 3, 0, 0, -1],
        [1, 0, 0, 3, 9, 3, 0, 0, -1],
        [1, 1, 0, 3, 9, 3, 0, 0, -1],
    ]
    # init input buffer, with data and transfer data list
    input_buffer = InputBuffer(256)
    input_buffer.add_transfer_data_list(data_list[1:2])
    # for communication example on the tile input buffer
    # judge part
    assert(input_buffer.check_remain_size() == 256 - 27)
    # communication start
    input_buffer.add_transfer_data_list(data_list[2:3])
    # communication end
    input_buffer.add_data_list(data_list[2:3])
    # for computation example on the tile input buffer
    # judge part
    assert input_buffer.check_data_already(data_list[2:3])
    # computation start, nothing
    # computation end
    input_buffer.delete_data_list(data_list[2:3])

    # init output buffer
    output_buffer = OutputBuffer(256)
    # for computation example on the tile output buffer
    # judge part
    assert(output_buffer.check_remain_size() == 256)
    # communication start, nothing
    # communication end
    output_buffer.add_data_list(data_list[0:1])
    # for communication example on the tile output buffer
    # judge part
    assert output_buffer.next_transfer_data() is not None
    # communication start, delete
    output_buffer.delete_data_list(data_list[0:1])
    # communication end, nothing
