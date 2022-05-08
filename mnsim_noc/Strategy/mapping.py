#-*-coding:utf-8-*-
"""
@FileName:
    mapping.py
@Description:
    mapping strategy for behavior driven simulation
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 20:43
"""
import abc
from mnsim_noc.utils.component import Component
from mnsim_noc.Tile import BaseTile
from mnsim_noc.Wire import WireNet
from mnsim_noc.Communication import BaseCommunication

class Mapping(Component):
    """
    mapping strategy for behavior driven simulation
    """
    REGISTRY = "mapping"
    def __init__(self, task_behavior_list, image_num,
        tile_net_shape, buffer_size, band_width
    ):
        super(Mapping, self).__init__()
        self.task_behavior_list = task_behavior_list
        self.image_num = image_num
        self.tile_row = tile_net_shape[0]
        self.tile_column = tile_net_shape[1]
        self.buffer_size = buffer_size
        self.band_width = band_width

    @abc.abstractmethod
    def _get_position_list(self, tile_behavior_list):
        """
        get position
        """
        raise NotImplementedError

    def mapping_net(self):
        """
        mapping net
        """
        tile_behavior_list = []
        for task_id, task_behavior in enumerate(self.task_behavior_list):
            # modify the tile task id and the last target
            task_behavior[-1]["target_tile_id"] = [-1]
            for tile_behavior in task_behavior:
                tile_behavior["task_id"] = task_id
                tile_behavior_list.append(tile_behavior)
        # get position
        position_list = self._get_position_list(tile_behavior_list)
        # get tile list
        tile_list = []
        for position, tile_behavior in zip(position_list, tile_behavior_list):
            tile = BaseTile(position, self.image_num, self.buffer_size, tile_behavior)
            tile_list.append(tile)
        # set buffer as start
        for tile in tile_list:
            if tile.layer_id == 0 and not tile.merge_flag:
                tile.input_buffer.set_start()
        # get wire net
        wire_net = WireNet((self.tile_row, self.tile_column), self.band_width)
        # communication list
        communication_list = []
        for start_tile in tile_list:
            end_tile_task_id = start_tile.task_id
            end_target_tile_id_list = start_tile.target_tile_id
            for end_tile in tile_list:
                if end_tile.task_id == end_tile_task_id \
                    and end_tile.tile_id in end_target_tile_id_list:
                    communication = BaseCommunication(start_tile, end_tile, wire_net)
                    communication_list.append(communication)
        return tile_list, communication_list, wire_net

    def get_update_order(self, tile_list, communication_list):
        """
        get update order, first write the read
        """
        update_module = []
        communication_in_ids = []
        for tile in tile_list:
            # first, communication output tile is this tile
            for communication in communication_list:
                if communication.output_tile is tile and id(communication) not in communication_in_ids:
                    communication_in_ids.append(id(communication))
                    update_module.append(communication)
            # this tile
            update_module.append(tile)
            # last for the communication input tile is this tile
            for communication in communication_list:
                if communication.input_tile is tile and id(communication) not in communication_in_ids:
                    communication_in_ids.append(id(communication))
                    update_module.append(communication)
        return update_module


class NaiveMapping(Mapping):
    """
    naive mapping
    """
    NAME = "naive"
    def _get_position_list(self, tile_behavior_list):
        """
        get position list
        """
        position_list = []
        for i in range(len(tile_behavior_list)):
            # get position
            position_row = i // self.tile_column
            position_column = i % self.tile_column
            position_list.append((position_row, position_column))
        return position_list
