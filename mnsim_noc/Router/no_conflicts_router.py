#-*-coding:utf-8-*-
"""
@FileName:
    no_conflicts_router.py
@Description:
    Router class for time slice without communication conflicts
@CreateTime:
    2021/10/22 16:00
"""
import re
import copy
from mnsim_noc.Router import BaseRouter
from mnsim_noc.Data.data import Data


class NoConflictsRouter(BaseRouter):
    NAME = "no_conflicts_router"

    def __init__(self, time_slice, packet_delay):
        super().__init__()
        self.wire_state = None
        self.paths = []
        # time_slice: span of a time_slice (ns)
        self.time_slice = time_slice
        # packet_delay: num of time slice needed for a packet to transfer through a wire
        self.packet_delay = packet_delay

    def assign(self, transfer_data, wire_state, tile_state, clock_num):
        """
        input:
            transfer_data: dict()[tile_id->tile.output]
            wire_state: useless
            tile_state: dict()[tile_id->(tile_input_cahe_is_full,tile.state)]
            clock_num: current clock_num in simulation
        Output:
            (routing results: paths)
        """
        # All paths arranged
        # path format: (list[occupied_wire_id], (x, y, end_tile_id, length, layer_out))
        self.paths = []
        # mark the occupation during routing
        for start_tile_id, tile_data in transfer_data.items():
            if not tile_data:
                continue
            # tile_data format:
            # (x, y, end_tile_id, length, layer_out)
            tile_input_cache_state = tile_state[tile_data.end_tile]
            if tile_input_cache_state[0]:
                self.logger.info('(Input Cache Occupied) layer:'+str(tile_data.layer_out)+' time:'+str(clock_num*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data.end_tile_id))
                continue
            # extract tile position from id
            start_tile_position = list(map(int, re.findall(r"\d+", start_tile_id)))
            end_tile_position = list(map(int, re.findall(r"\d+", tile_data.end_tile_id)))
            step_x = end_tile_position[0]-start_tile_position[0]
            step_y = end_tile_position[1]-start_tile_position[1]
            length = int(tile_data.length)
            tile_data.length = length
            # North:0; West:1; South:2; East:3;
            direction_x = 2 if step_x > 0 else 0
            ceil_x = 1 if step_x > 0 else -1
            direction_y = 3 if step_y > 0 else 1
            ceil_y = 1 if step_y > 0 else -1
            # Routing algorithm: first in x, then in y, no communication conflicts
            # Search for possible paths
            current_path = []
            current_position = start_tile_position.copy()
            wait_time_tmp = 0
            # go in x
            for i in range(1, abs(step_x)+1):
                current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_x)
                current_path.append(current_wire_id)
                current_position[0] += ceil_x
                wait_time_tmp += self.packet_delay
            # go in y
            for i in range(1, abs(step_y)+1):
                current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_y)
                current_path.append(current_wire_id)
                current_position[1] += ceil_y
                wait_time_tmp += self.packet_delay
            self.paths.append((current_path, tile_data))
            # log the transfer layer and time(ns)
            self.logger.info('(Transfer) layer:'+str(tile_data.layer_out)+' start:'+str(clock_num*self.time_slice)+' finish:'+str((clock_num+tile_data.length)*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data.end_tile_id)+' data:'+str((tile_data.x,tile_data.y)))
        return self.paths
