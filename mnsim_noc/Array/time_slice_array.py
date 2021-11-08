# -*-coding:utf-8-*-
"""
@FileName:
    time_slice_tile.py
@Description:
    Array class for time slice
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2021/10/08 18:28
"""
import re
import configparser as cp
from mnsim_noc.Array import BaseArray
from mnsim_noc.Tile import FCTimeSliceTile, CONVTimeSliceTile, PoolingTimeSliceTile
from mnsim_noc.Wire import TimeSliceWire
from mnsim_noc.Router import TimeSliceRouter


class TimeSliceArray(BaseArray):
    NAME = "time_slice_array"
    '''
    array_cfg: 
    time_slice: span of a time_slice (ns)
    sim_config_path: hardware description
    '''
    def __init__(self, tcg_mapping, time_slice, sim_config_path):
        super().__init__(self, tcg_mapping)
        # 切片时长: ns
        self.time_slice = time_slice
        tcg_config = cp.ConfigParser()
        tcg_config.read(sim_config_path, encoding='UTF-8')
        # 传输线带宽: Gbps
        self.bandwidth = int(tcg_config.get('Tile level', 'Inter_Tile_Bandwidth'))
        self.clock_num = 0
        self.tile_dict = dict()
        self.wire_dict = dict()
        self.wire_data_transferred = dict()
        self.layer_cfg = []

    def task_assignment(self):
        # Convert the layer_info
        for layer_id in range(self.tcg_mapping.layer_num):
            layer_dict = self.tcg_mapping.net[layer_id][0][0]
            cfg = dict()
            # TODO: extended to support branch
            # can be extended to support branch
            cfg['length'] = int(layer_dict['Outputchannel']) * int(
                layer_dict['outputbit']) / self.bandwidth / self.time_slice
            if len(self.tcg_mapping.layer_tileinfo[layer_id]['Inputindex']) > 1:
                self.logger.warn('Do not support branch')
            cfg['layer_in'] = self.tcg_mapping.layer_tileinfo[layer_id]['Inputindex'][0] + layer_id
            if len(self.tcg_mapping.layer_tileinfo[layer_id]['Outputindex']) > 1:
                self.logger.warn('Do not support branch')
            cfg['tile_out'] = self.tcg_mapping.layer_tileinfo[layer_id]['Outputindex'][0] + layer_id
            cfg['layer_out'] = layer_id
            cfg['tile_num'] = self.tcg_mapping.layer_tileinfo[layer_id]['tilenum']
            cfg['tile_id'] = []
            cfg['aggregate_arg'] = self.tcg_mapping.aggregate_arg[layer_id]
            # cfg['computing_time']
            # cfg['end_tiles']
            if layer_dict['type'] == 'conv':
                cfg['type'] = 'conv'
                cfg['height_input'] = layer_dict['Inputsize'][0]
                cfg['width_input'] = layer_dict['Inputsize'][1]
                cfg['height_output'] = layer_dict['Outputsize'][0]
                cfg['width_output'] = layer_dict['Outputsize'][1]
                cfg['height_core'] = layer_dict['Kernelsize']
                cfg['width_core'] = layer_dict['Kernelsize']
            elif layer_dict['type'] == 'pooling':
                cfg['type'] = 'pooling'
                cfg['height_input'] = layer_dict['Inputsize'][0]
                cfg['width_input'] = layer_dict['Inputsize'][1]
                cfg['height_output'] = layer_dict['Outputsize'][0]
                cfg['width_output'] = layer_dict['Outputsize'][1]
                cfg['height_filter'] = layer_dict['Kernelsize']
                cfg['width_filter'] = layer_dict['Kernelsize']
            elif layer_dict['type'] == 'fc':
                cfg['type'] = 'fc'
                cfg['height_input'] = layer_dict['Infeature']
                cfg['width_input'] = 0
                cfg['height_output'] = layer_dict['Outfeature']
                cfg['width_output'] = 0
            else:
                self.logger.warn('Unsupported layer type, layer_id:' + str(layer_id))
            self.layer_cfg.append(cfg)
        # generate tile_ids and aggregate_arg for layers
        for i in range(self.tcg_mapping.tile_num[0]):
            for j in range(self.tcg_mapping.tile_num[1]):
                layer_id = self.tcg_mapping.mapping_result[i][j]
                self.layer_cfg[layer_id]['tile_id'].append("{}_{}".format(i, j))
        # allocate the tiles
        for i in range(self.tcg_mapping.tile_num[0]):
            for j in range(self.tcg_mapping.tile_num[1]):
                layer_id = self.tcg_mapping.mapping_result[i][j]
                cfg = self.layer_cfg[layer_id]
                # TODO: extended to support branch
                # process the aggregate tile
                if (cfg['aggregate_arg'][0], cfg['aggregate_arg'][1]) == (i, j):
                    cfg['end_tiles'] = self.layer_cfg[cfg['tile_out']]['tile_id']
                    cfg['num_out'] = cfg['tile_num']
                else:
                    cfg['end_tiles'] = "{}_{}".format(cfg['aggregate_arg'][0], cfg['aggregate_arg'][1])
                    cfg['num_out'] = 1
                    cfg['length'] = round(cfg['length'] / cfg['tile_num'])
                # different tile types
                if cfg['type'] == 'conv':
                    tile = CONVTimeSliceTile((i, j), cfg)
                elif cfg['type'] == 'fc':
                    tile = FCTimeSliceTile((i, j), cfg)
                elif cfg['type'] == 'pooling':
                    tile = PoolingTimeSliceTile((i, j), cfg)
                self.tile_dict[tile.tile_id] = tile
        # allocate the wires
        for i in range(self.tcg_mapping.tile_num[0]):
            for j in range(self.tcg_mapping.tile_num[1]):
                # North:0; West:1; South:2; East:3;
                if i > 0:
                    wire = TimeSliceWire((i, j, 0))
                    self.wire_dict[wire.wire_id] = wire
                if j > 0:
                    wire = TimeSliceWire((i, j, 1))
                    self.wire_dict[wire.wire_id] = wire
                if i < self.tcg_mapping.tile_num[0] - 1:
                    wire = TimeSliceWire((i, j, 2))
                    self.wire_dict[wire.wire_id] = wire
                if j < self.tcg_mapping.tile_num[1] - 1:
                    wire = TimeSliceWire((i, j, 3))
                    self.wire_dict[wire.wire_id] = wire
        # allocate the router
        self.router = TimeSliceRouter()
        # distribute inputs for tiles in layer_0
        inputs_inits = []
        if self.layer_cfg[0]['type'] == 'conv' or self.layer_cfg[0]['type'] == 'pooling':
            for x in range(self.layer_cfg[0]['height_input']):
                for y in range(self.layer_cfg[0]['width_input']):
                    inputs_inits.append((x + 1, y + 1, -1))
        elif self.layer_cfg[0]['type'] == 'fc':
            for x in range(self.layer_cfg[0]['height_input']):
                inputs_inits.append((x + 1, -1, -1))
        for tile_id in self.layer_cfg[0]['tile_id']:
            self.tile_dict[tile_id].update_input(self, inputs_inits)

    def check_finish(self):
        for tile_id, tile in self.tile_dict.items():
            if tile.input_list or tile.output_list:
                return False
        for wire_id, wire in self.wire_dict.items():
            if wire.state:
                return False
        return True

    def set_wire_task(self, routing_result):
        # task format: (x, y, end_tile_id, length, layer, is_first, is_last)
        # path format: (list[occupied_wire_id], (x, y, end_tile_id, length, layer_out))
        for path in routing_result:
            wire_list = path[0]
            path_data = path[1]
            wire_len = len(wire_list)
            for index, wire_id in enumerate(wire_list):
                is_first = (index == 0)
                is_last = (index == wire_len - 1)
                self.wire_dict[wire_id].set_wire_task(path_data + (is_first, is_last))

    def update_tile(self):
        for wire_id, wire_data in self.wire_data_transferred.items():
            if wire_data:
                # wire_data format: (x, y, end_tile_id, layer, is_first, is_last)
                if wire_data[4]:
                    wire_position = tuple(map(int, re.findall(r"\d+", wire_id)))
                    tile_id = "{}_{}".format(wire_position[0], wire_position[1])
                    self.tile_dict[tile_id].update_output([wire_data[0:3]])
                if wire_data[5]:
                    tile_id = wire_data[2]
                    self.tile_dict[tile_id].update_input([wire_data[0:2] + wire_data[3]])

    def run(self):
        # task assignment
        self.task_assignment()
        # run for every slice
        while True:
            if self.check_finish():
                break
            # 0, all tile and wire update for one slice
            for tile_id, tile in self.tile_dict.items():
                tile.update_time_slice()
            # get the data transferred by wires
            self.wire_data_transferred = dict()
            for wire_id, wire in self.wire_dict.items():
                self.wire_data_transferred[wire_id] = wire.update_time_slice()
            # 1, update tile input and output
            self.update_tile()
            # 2, get all transfer data
            transfer_data = dict()
            for tile_id, tile in self.tile_dict.items():
                # transfer_data format: (x, y, end_tile_id, length, layer_out)
                transfer_data[tile_id] = tile.get_output()
            # 3, get all wire state
            wire_state = dict()
            for wire_id, wire in self.wire_dict.items():
                wire_state[wire_id] = wire.state
            # 4, routing
            # path format: (list[occupied_wire_id], (x, y, end_tile_id, length, layer_out))
            routing_result = self.router.assign(transfer_data, wire_state)
            # 5, set wire task
            self.set_wire_task(routing_result)
            # 6, record clock_num
            self.clock_num = self.clock_num + 1
        # print the simulation time
        self.logger.log('Compute Time: ' + str(self.clock_num * self.time_slice / 1000000) + 'ms')
