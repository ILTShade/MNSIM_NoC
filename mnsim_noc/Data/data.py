#-*-coding:utf-8-*-
"""
@FileName:
    data.py
@Description:
    Data class
@CreateTime:
    2021/10/08 18:46
"""
from abc import abstractmethod
from mnsim_noc.base import Component


class Data(Component):
    REGISTRY = "data"

    def __init__(self,x=0,y=0,layer_out=0,length=0,image_id=0,end_tile_id=''):
        super().__init__()
        # location on the feature map
        self.x = x
        self.y = y
        # layer_out
        self.layer_out = layer_out
        # data length
        self.length = length
        # id of the input image data
        self.image_id = image_id
        # end_tile
        self.end_tile_id = end_tile_id
        # is first/last
        self.is_first = False
        self.is_last = False