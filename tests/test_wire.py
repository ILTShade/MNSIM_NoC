#-*-coding:utf-8-*-
"""
@FileName:
    test_wire.py
@Description:
    test wire net class
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 17:33
"""
from mnsim_noc.Wire import WireNet

def test_wire():
    """
    test wire net class
    """
    wire_net = WireNet((2, 2), 1)
    wire_net.set_transparent_flag(True)