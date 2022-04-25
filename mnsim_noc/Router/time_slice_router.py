#-*-coding:utf-8-*-
"""
@FileName:
    time_slice_router.py
@Description:
    Router class for time slice
@CreateTime:
    2021/10/22 16:00
"""
import re
import copy
from mnsim_noc.Router import BaseRouter
from mnsim_noc.Data.data import Data


class TimeSliceRouter(BaseRouter):
    NAME = "time_slice_router"

    def __init__(self, time_slice, packet_delay, quiet):
        super().__init__(quiet)
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
            wire_state: dict()[wire_id->wire.state]
            tile_state: dict()[tile_id->(tile.input_cache_full(), tile.state, tile.input_image_id, tile.output_image_id, tile.layer_in, tile.layer_out)]
            clock_num: current clock_num in simulation
        Output:
            (routing results: paths, refused routing with backtime)
        """
        # All paths arranged
        # path format: (list[occupied_wire_id], (x, y, end_tile_id, length, layer_out))
        self.paths = []
        # mark the occupation during routing
        self.wire_state = wire_state
        for start_tile_id, tile_data in transfer_data.items():
            if not tile_data:
                continue
            # tile_data format:
            # (x, y, end_tile_id, length, layer_out)
            tile_input_cache_state = tile_state[tile_data.end_tile_id]
            if tile_input_cache_state[0]:
                if not self.quiet:
                    self.logger.info('(Input Cache Occupied) image_id:'+str(tile_data.image_id)+' layer:'+str(tile_data.layer_out)+' time:'+str(clock_num*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data.end_tile_id))
                continue
            if tile_input_cache_state[4] == tile_data.layer_out:
                if tile_data.image_id != tile_input_cache_state[2]:
                    if not self.quiet:
                        self.logger.warn('(wrong image_id) image_id:'+str(tile_data.image_id)+' layer:'+str(tile_data.layer_out)+' time:'+str(clock_num*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data.end_tile_id))
                    continue
            elif tile_input_cache_state[5] == tile_data.layer_out:
                if tile_data.image_id > tile_input_cache_state[3]:
                    if not self.quiet:
                        self.logger.warn('(wrong image_id) image_id:'+str(tile_data.image_id)+' layer:'+str(tile_data.layer_out)+' time:'+str(clock_num*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data.end_tile_id))
                    continue
            else:
                self.logger.warn('(wrong layer) image_id:'+str(tile_data.image_id)+' layer:'+str(tile_data.layer_out)+' time:'+str(clock_num*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data.end_tile_id))
                exit()
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
            # Routing algorithm: first in x, then in y, last in x, choose the first possible path
            # Search for possible paths
            current_path = []
            for i in range(0, abs(step_x)+1):
                current_position = start_tile_position.copy()
                path_failed = False
                wait_time_tmp = 0
                # go i steps in x
                for j in range(1, i+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_x)
                    if self.wire_state[current_wire_id][2] <= wait_time_tmp and self.wire_state[current_wire_id][0]:
                        current_path.append(current_wire_id)
                        current_position[0] += ceil_x
                    else:
                        path_failed = True
                        break
                    wait_time_tmp += self.packet_delay
                if path_failed:
                    current_path.clear()
                    continue
                # go in y
                for j in range(1, abs(step_y)+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_y)
                    if self.wire_state[current_wire_id][2] <= wait_time_tmp and self.wire_state[current_wire_id][0]:
                        current_path.append(current_wire_id)
                        current_position[1] += ceil_y
                    else:
                        path_failed = True
                        break
                    wait_time_tmp += self.packet_delay
                if path_failed:
                    current_path.clear()
                    continue
                # go abs(step_x)-i steps in x
                for j in range(1, abs(step_x)-i+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_x)
                    if self.wire_state[current_wire_id][2] <= wait_time_tmp and self.wire_state[current_wire_id][0]:
                        current_path.append(current_wire_id)
                        current_position[0] += ceil_x
                    else:
                        path_failed = True
                        break
                    wait_time_tmp += self.packet_delay
                if path_failed:
                    current_path.clear()
                    continue
                break
            if current_path:
                self.paths.append((current_path, tile_data))
                # log the transfer layer and time(ns)
                # TODO: 改变传输结束时间估计
                if not self.quiet:
                    self.logger.info('(Transfer) image_id:'+str(tile_data.image_id)+' layer:'+str(tile_data.layer_out)+' start:'+str(clock_num*self.time_slice)+' finish:'+str((clock_num+tile_data.length)*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data.end_tile_id)+' data:'+str((tile_data.x,tile_data.y)))
                for path_wire_id in current_path:
                    self.wire_state[path_wire_id] = (False, self.wire_state[path_wire_id][1], self.wire_state[path_wire_id][2])
            else:
                if not self.quiet:
                    self.logger.info('(Wire Occupied) image_id:'+str(tile_data.image_id)+' layer:'+str(tile_data.layer_out)+' time:'+str(clock_num*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data.end_tile_id))
        return self.paths
