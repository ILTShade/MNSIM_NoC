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

    def __init__(self):
        super().__init__()
        self.wire_state = None
        self.paths = []

    def assign(self, transfer_data, wire_state):
        """
        input:
            transfer_data: dict()[tile_id->tile.output]
            wire_state: dict()[wire_id->wire.state]
        Output:
            routing results: paths
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
            # extract tile position from id
            start_tile_position = list(map(int, re.findall(r"\d+", start_tile_id)))
            end_tile_position = list(map(int, re.findall(r"\d+", tile_data[2])))
            step_x = end_tile_position[0]-start_tile_position[0]
            step_y = end_tile_position[1]-start_tile_position[1]
            # North:0; West:1; South:2; East:3;
            direction_x = 2 if step_x > 0 else 0
            direction_y = 3 if step_y > 0 else 1
            # Routing algorithm: first in x, then in y, last in x, choose the first possible path
            # Search for possible paths
            current_path = []
            for i in range(0, abs(step_x)+1):
                current_position = start_tile_position
                path_failed = False
                # go i steps in x
                for j in range(1, i+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_x)
                    if self.wire_state[current_wire_id] == 0:
                        current_path.append(current_wire_id)
                        current_position[0] += 1
                    else:
                        path_failed = True
                        break
                if path_failed:
                    current_path.clear()
                    continue
                # go in y
                for j in range(1, abs(step_y)+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_y)
                    if self.wire_state[current_wire_id] == 0:
                        current_path.append(current_wire_id)
                        current_position[1] += 1
                    else:
                        path_failed = True
                        break
                if path_failed:
                    current_path.clear()
                    continue
                # go abs(step_x)-i steps in x
                for j in range(1, abs(step_x)-i+1):
                    current_wire_id = "{}_{}_{}".format(current_position[0], current_position[1], direction_x)
                    if self.wire_state[current_wire_id] == 0:
                        current_path.append(current_wire_id)
                        current_position[0] += 1
                    else:
                        path_failed = True
                        break
                if path_failed:
                    current_path.clear()
                    continue
                break
            if current_path:
                self.paths.append((current_path, tile_data))
                print('Routed: '+str(tile_data))
                for path_wire_id in current_path:
                    self.wire_state[path_wire_id] = 1
        return self.paths
