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
from mnsim_noc.Router import BaseRouter


class TimeSliceRouter(BaseRouter):
    NAME = "time_slice_tile"

    def __init__(self, time_slice):
        super().__init__()
        self.wire_state = None
        self.paths = []
        self.refused = []
        # time_slice: span of a time_slice (ns)
        self.time_slice = time_slice

    def assign(self, transfer_data, wire_state, tile_state, clock_num):
        """
        input:
            transfer_data: dict()[tile_id->tile.output]
            wire_state: dict()[wire_id->wire.state]
            tile_state: dict()[tile_id->(tile_input_cahe_is_full,tile.state)]
            clock_num: current clock_num in simulation
        Output:
            (routing results: paths, refused routing with backtime)
        """
        # All paths arranged
        # path format: (list[occupied_wire_id], (x, y, end_tile_id, length, layer_out))
        self.paths = []
        # refused routing format: (start_tile_id, backtime)
        self.refused = []
        # mark the occupation during routing
        self.wire_state = wire_state
        for start_tile_id, tile_data in transfer_data.items():
            if not tile_data:
                continue
            # tile_data format:
            # (x, y, end_tile_id, length, layer_out)
            tile_input_cache_state = tile_state[tile_data[2]]
            if tile_input_cache_state[0]:
                self.refused.append((start_tile_id, tile_input_cache_state[1]))
                self.logger.info('(Input Cache Occupied) layer:'+str(tile_data[4])+' time:'+str(clock_num*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(tile_data[2]))
                continue
            # extract tile position from id
            start_tile_position = list(map(int, re.findall(r"\d+", start_tile_id)))
            end_tile_position = list(map(int, re.findall(r"\d+", tile_data[2])))
            step_x = end_tile_position[0]-start_tile_position[0]
            step_y = end_tile_position[1]-start_tile_position[1]
            length = round(tile_data[3]*(abs(step_x)+abs(step_y)))
            data = tile_data[0:3]+(length,tile_data[4])
            # North:0; West:1; South:2; East:3;
            direction_x = 2 if step_x > 0 else 0
            direction_y = 3 if step_y > 0 else 1
            # Routing algorithm: first in x, then in y, last in x, choose the first possible path
            # Search for possible paths
            current_path = []
            backtime = float("inf")
            for i in range(0, abs(step_x)+1):
                current_position = start_tile_position
                path_failed = False
                backtime_tmp = 0
                # go i steps in x
                for j in range(1, i+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_x)
                    backtime_tmp = max(backtime_tmp, self.wire_state[current_wire_id])
                    if self.wire_state[current_wire_id] == 0:
                        current_path.append(current_wire_id)
                        current_position[0] += 1
                    else:
                        path_failed = True
                        break
                if path_failed:
                    current_path.clear()
                    backtime = min(backtime, backtime_tmp)
                    continue
                # go in y
                for j in range(1, abs(step_y)+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_y)
                    backtime_tmp = max(backtime_tmp, self.wire_state[current_wire_id])
                    if self.wire_state[current_wire_id] == 0:
                        current_path.append(current_wire_id)
                        current_position[1] += 1
                    else:
                        path_failed = True
                        break
                if path_failed:
                    current_path.clear()
                    backtime = min(backtime, backtime_tmp)
                    continue
                # go abs(step_x)-i steps in x
                for j in range(1, abs(step_x)-i+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_x)
                    backtime_tmp = max(backtime_tmp, self.wire_state[current_wire_id])
                    if self.wire_state[current_wire_id] == 0:
                        current_path.append(current_wire_id)
                        current_position[0] += 1
                    else:
                        path_failed = True
                        break
                if path_failed:
                    current_path.clear()
                    backtime = min(backtime, backtime_tmp)
                    continue
                break
            if current_path:
                self.paths.append((current_path, data))
                # log the transfer layer and time(ns)
                self.logger.info('(Transfer) layer:'+str(data[4])+' start:'+str(clock_num*self.time_slice)+' finish:'+str((clock_num+data[3])*self.time_slice))
                for path_wire_id in current_path:
                    self.wire_state[path_wire_id] = 1
            else:
                self.refused.append((start_tile_id, int(backtime)))
                self.logger.info('(Wire Occupied) layer:'+str(data[4])+' time:'+str(clock_num*self.time_slice)+' start_tile:'+str(start_tile_id)+' end_tile:'+str(data[2]))
        return self.paths, self.refused
