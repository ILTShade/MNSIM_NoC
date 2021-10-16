# -*-coding:utf-8-*-
"""
@FileName:
    time_slice_tile.py
@Description:
    Tile class for time slice
@CreateTime:
    2021/10/17 10:00
"""
from mnsim_noc.Tile import BaseTile


class TimeSliceTile(BaseTile):
    NAME = "time_slice_tile"

    def __init__(self, position, task_cfg):
        # input and output data
        # format: (start_tile_id, end_tile_id, layer, x, y, length)
        super().__init__(self, position, task_cfg)
        # Tile在网络中的层数
        self.layer_in = task_cfg.layer_in
        self.layer_out = task_cfg.layer_out
        # Tile需要几个输入
        self.num_in = task_cfg.num_in
        # 用字典记录同点输入已传入个数
        self.input_to_be_merged = dict()
        # 维护最新输入坐标
        self.latest_input = (0, 0)
        # Tile对应的网络种类
        self.type = task_cfg.type
        # 卷积核参数
        self.height_core = task_cfg.height_core
        self.width_core = task_cfg.width_core
        self.stride_core = task_cfg.stride_core
        self.padding_core = task_cfg.padding_core
        # 输入特征图参数
        self.height_input = task_cfg.height_input
        self.width_input = task_cfg.width_input
        # 输出广播Tile坐标列表
        self.nodes_out = task_cfg.nodes_out
        # 计算中的输出（输出特征图坐标）
        self.computing_output = None
        # 下次计算的输出坐标
        self.next_output = (1, 1)
        # 无用输入最右下角的范围
        self.useless = (0, 0)

    def update_input(self, inputs):
        # inputs格式只需要特征图上的坐标即可,用元组实现
        if self.num_in == 1:
            self.input_list.extend(inputs)
        else:
            for single_input in inputs:
                # 若已有同位置输入
                if single_input in self.input_to_be_merged:
                    # 获取当前输入个数
                    current_num = self.input_to_be_merged[single_input]
                    # 若输入数量已经足够
                    if current_num == self.num_in - 1:
                        self.input_list.append(single_input)
                        # 维护最新输入范围以简化操作
                        self.latest_input = single_input
                        del self.input_to_be_merged[single_input]
                    else:
                        self.input_to_be_merged[single_input] = current_num + 1
                # 若为同位置第一次输入
                else:
                    self.input_to_be_merged[single_input] = 1

    def update_time_slice(self):
        # 若当前无计算任务（空闲/已完成）
        if self.state == 0:
            # 已完成任务，则更新输出列表
            if self.computing_output:
                # TODO: 根据self.useless删除列表中所有无用输入
                self.output_list.append(self.computing_output)
                self.computing_output = None
            # 有未计算的输入，则分配新的计算任务
            if self.input_list:
                if self.type == "CONV":
                    x_req = min(self.height_input,
                                self.height_core + self.stride_core * (self.next_output[0] - 1) - self.padding_core)
                    y_req = min(self.width_input,
                                self.width_core + self.stride_core * (self.next_output[1] - 1) - self.padding_core)
                    # 若满足下次输出需求
                    if (self.latest_input[0] * self.width_input + self.latest_input[1]) >= (
                            x_req * self.width_input + y_req):
                        # TODO: 更新self.useless
                        # TODO: 更新self.computing_output
                        # TODO: 更新self.next_output
                        pass
                elif self.type == "FC":
                    pass
                elif self.type == "Merge":
                    pass
        else:
            self.state -= 1

    def update_output(self):
        pass
