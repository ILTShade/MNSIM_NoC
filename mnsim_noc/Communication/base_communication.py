#-*-coding:utf-8-*-
"""
@FileName:
    base_communication.py
@Description:
    base communication class for behavior-driven simulation
@Authors:
    Hanbo Sun(sun-hb17@mails.tsinghua.edu.cn)
@CreateTime:
    2022/05/07 17:38
"""
from mnsim_noc.utils.component import Component
from mnsim_noc.Tile import BaseTile
from mnsim_noc.Wire import WireNet
from mnsim_noc.Buffer.base_buffer import get_data_size

class BaseCommunication(Component):
    """
    base communication class for behavior-driven simulation
    """
    REGISTRY = "communication"
    NAME = "behavior-driven"
    def __init__(self, input_tile: BaseTile, output_tile: BaseTile, wire_net: WireNet):
        """
        init base communication
        data from input tile to output tile
        """
        super(BaseCommunication, self).__init__()
        # set input tile and output tile
        self.input_tile = input_tile
        self.output_tile = output_tile
        self.wire_net = wire_net
        # input buffer and output buffer, for tile
        self.output_buffer = self.input_tile.output_buffer
        self.input_buffer = self.output_tile.input_buffer
        self.target_tile_id = self.output_tile.tile_id
        self.source_tile_id = self.input_tile.tile_id
        # state
        self.running_state = False
        self.communication_end_time = float("inf")
        self.communication_range_time = []
        # transfer data and path
        self.transfer_data = None
        self.transfer_path = None
        # transfer rate
        self.number_total_communication = self.input_tile.image_num * \
            len(self.input_tile.tile_behavior_cfg["dependence"])
        self.number_done_communication = 0
        # set communication id
        self.communication_id = \
            f"{input_tile.task_id},{input_tile.tile_id}"+\
            f"->{output_tile.task_id},{output_tile.tile_id}"

    def update(self, current_time):
        """
        since there may be multiple communication
        only change running state from True to False
        """
        if self.running_state:
            if current_time >= self.communication_end_time:
                # PHASE COMMUNICATION END
                # NO next communication
                self.running_state = False
                self.input_buffer.add_data_list(self.transfer_data, self.source_tile_id)
                # clear transfer data path
                self.wire_net.set_data_path_state(
                    self.transfer_path, False, self.communication_id, current_time
                )
                # add number of done communication
                self.number_done_communication += 1

    def check_communication_ready(self):
        """
        check if this communication can transfer data
        """
        # there may be larger for the tile input buffer
        if self.running_state:
            return False
        # PHASE COMMUNICATION JUDGE
        self.transfer_data = self.output_buffer.next_transfer_data(self.target_tile_id)
        if self.transfer_data is not None \
            and self.input_buffer.check_enough_space(self.transfer_data, self.source_tile_id):
            return True
        return False

    def set_communication_task(self, current_time, trasnfer_path, transfer_time):
        """
        transfer path can be None, means no communication
        """
        assert trasnfer_path is not None
        assert not self.running_state, f"communication should be idle"
        # PHASE COMMUNICATION START
        self.running_state = True
        self.transfer_path = trasnfer_path
        # set buffer
        self.input_buffer.add_transfer_data_list(self.transfer_data, self.source_tile_id)
        self.output_buffer.delete_data_list(self.transfer_data, self.target_tile_id)
        # get transfet time
        self.communication_end_time = current_time + transfer_time
        self.communication_range_time.append((current_time, self.communication_end_time))
        # set wire state, in schedule
        self.wire_net.set_data_path_state(
            self.transfer_path, True, self.communication_id, current_time
        )

    def get_communication_end_time(self):
        """
        get the end time of the communication
        """
        if self.running_state:
            return self.communication_end_time
        return float("inf")

    def get_communication_range(self):
        """
        get the range of the communication
        """
        return self.communication_range_time

    def get_done_communication_rate(self):
        """
        get the done communication rate
        """
        return self.number_done_communication * 1. / self.number_total_communication

    def check_finish(self):
        """
        check if the communication is finish
        """
        assert self.running_state == False, "communication should be idle"
        assert self.get_communication_end_time() == float("inf"), \
            "communication end time should be inf"
        assert self.number_done_communication == self.number_total_communication, \
            "number of done communication should be equal to total communication"

    def get_running_rate(self, end_time):
        """
        get the simulation result
        """
        self.check_finish()
        communication_time = sum([
            end - start for start, end in self.communication_range_time
        ])
        return communication_time * 1. / end_time

    def get_residual_data(self):
        """
        get the residual data count
        """
        assert self.input_tile.image_num == 1, f"only support image num 1"
        residual_data = 0.
        for i in range(self.number_done_communication, self.number_total_communication):
            for s in self.input_tile.tile_behavior_cfg["dependence"][i]["output"]:
                residual_data += get_data_size(s)
        # total
        total_data = 0.
        for i in range(self.number_done_communication):
            for s in self.input_tile.tile_behavior_cfg["dependence"][i]["output"]:
                total_data += get_data_size(s)
        if total_data == 0.:
            return 0.
        return residual_data ** 2 / total_data
