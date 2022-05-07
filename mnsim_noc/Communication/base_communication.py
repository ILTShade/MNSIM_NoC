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
        # state
        self.running_state = False
        self.communication_end_time = float("inf")
        self.communication_range_time = []
        # transfer data and path
        self.transfer_data = None
        self.transfer_path = None

    def update(self, current_time):
        """
        since there may be multiple communication
        only change running state from True to False
        """
        if self.running_state:
            if current_time >= self.communication_end_time:
                # NO next communication
                self.running_state = False
                self.input_buffer.add_data_list(self.transfer_data)
                # clear transfer data path
                self.wire_net.set_data_path_state(self.transfer_path, False)

    def check_communication_ready(self):
        """
        check if this communication can transfer data
        """
        # TODO: there may be larger for the tile input buffer
        if self.running_state:
            return False
        self.transfer_data = self.output_buffer.next_transfer_data()
        if self.transfer_data is not None \
            and self.input_buffer.check_enough_space(self.transfer_data):
            return True
        return False

    def set_communication_task(self, current_time, trasnfer_path):
        """
        transfer path can be None, means no communication
        """
        if trasnfer_path is None:
            if self.running_state == False:
                self.communication_end_time = float("inf")
            return None
        assert not self.running_state, f"communication should be idle"
        self.running_state = True
        self.transfer_path = trasnfer_path
        # set buffer
        self.input_buffer.add_transfer_data_list(self.transfer_data)
        self.output_buffer.delete_data_list(self.transfer_data)
        # get transfet time
        transfer_time = self.wire_net.get_wire_transfer_time(trasnfer_path, self.transfer_data)
        assert transfer_time > 0, "transfer time should be positive"
        self.communication_end_time = current_time + transfer_time
        self.communication_range_time.append((current_time, self.communication_end_time))
        # set wire state, in schedule
        # self.wire_net.set_data_path_state(self.transfer_path, True)

    def get_communication_end_time(self):
        """
        get the end time of the communication
        """
        if self.running_state:
            return self.communication_end_time
        else:
            return float("inf")

    def get_communication_range(self):
        """
        get the range of the communication
        """
        return self.communication_range_time
