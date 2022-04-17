# -*-coding:utf-8-*-
"""
@FileName:
    time_slice_wire.py
@Description:
    Wire Class for time slice
@CreateTime:
    ---
"""
from mnsim_noc.Wire import BaseWire


class TimeSliceWire(BaseWire):
    NAME = "time_slice_wire"

    def __init__(self, position):
        super().__init__(position)
        # data transmitted on the wire
        # format: (x, y, end_tile_id, layer)
        self.data = None
        # Number of time slice required for finishing the transmission
        self.state = 0
        # data transferred during simulation
        self.transferred_data = 0
        # the date to be transferred
        self.next_data = None
        # wait time to apply next data
        self.wait_time = 0

    def set_wire_task(self, wire_tasks, wait_time):
        # Format:(x, y, end_tile_id, length, layer, is_first, is_last)
        self.wait_time = wait_time
        # data Format:(x, y, end_tile_id, layer, is_first, is_last)
        self.next_data = wire_tasks
        self.transferred_data += wire_tasks.length
        # if self.data and self.next_data and self.state > self.wait_time:
        #     self.logger.warn("(Wrong wire behaviour) state:"+str(self.state)+' wait_time:'+str(self.wait_time))
        #     exit()
        # else:
        #     self.logger.info("(Wire task set) state:"+str(self.state)+' wait_time:'+str(self.wait_time))
        if self.wait_time == 0 and self.next_data and not self.data:
            self.state = self.next_data.length
            self.data = self.next_data
            self.next_data = None
            self.wait_time = 0

    def update_time_slice(self, n):
        if self.state > 0:
            self.state -= n
        if self.state == 0 and self.data:
            # return data to update tile
            tmp_data = [self.data]
            self.data = None
        else: 
            tmp_data = []
        if self.wait_time > 0:
            self.wait_time -= n
        if self.wait_time == 0 and self.next_data and not self.data:
            self.state = self.next_data.length
            self.data = self.next_data
            self.next_data = None
            self.wait_time = 0
        return tmp_data

    def get_roofline(self):
        return int(self.transferred_data)

    def get_wait_time(self):
        # get the end time of occupation
        return self.wait_time, self.state

    def get_timeslice_num(self):
        # get the next timeslice num
        tmp_timeslice_num = float("inf")
        if self.data:
            tmp_timeslice_num =  min(max(1,self.state), tmp_timeslice_num)
        if self.next_data:
            tmp_timeslice_num =  min(max(1,self.wait_time), tmp_timeslice_num)
        return tmp_timeslice_num

    def check_finish(self):
        if self.state > 0 or self.wait_time > 0:
            return False
        else:
            return True