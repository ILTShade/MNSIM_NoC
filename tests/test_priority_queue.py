#-*-coding:utf-8-*-
"""
@FileName:
    test_priority_queue.py
@Description:
    test priority queue
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2023/05/08 11:59
"""
from mnsim_noc.Wire.wire_net import _MyPriorityQueue

def test_priority_queue():
    """
    test priority queue
    """
    priority_queue = _MyPriorityQueue(100)
    input_list = [
        (1, "a"), (9, "b"), (4, "c"),
        (5, "d"), (4, "e"), (5, "f"),
        (7, "g"), (6, "h"), (4, "i")
    ]
    for item in input_list:
        priority_queue.put(item)
        print(f"-" * 20)
        print(f"put item {item}")
        print(f"priority queue is {priority_queue.queue[:10]}")
