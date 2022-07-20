#!/usr/bin/env python3

## Live Plotting Tool for Serial Stream Data
## Scott Park, June 2022

import serial
import os
import sys
import time
import json
import threading
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
matplotlib.use('Qt5Agg')
from collections import namedtuple
from dataclasses import dataclass, field
from typing import List, Callable, Dict

class StreamConfig:
    ''' 
    Class for configuring expected streamed data format 

    Example:
    
        Data:

        0;10006;10011;09961;50248;00001;00000;30000;00000;30000;50241;00501;00012;00008;00000;00100;\r\n
        0;10012;10011;09961;50252;00001;00000;30000;00000;30000;50240;00501;00012;00008;00000;00100;\r\n
        0;10009;10011;09961;50249;00001;00000;30000;00000;30000;50240;00501;00012;00008;00000;00100;\r\n
        0;10011;10011;09961;50251;00001;00000;30000;00000;30000;50240;00553;00012;00008;00000;00100;\r\n
        0;10011;10011;09961;50247;00001;00000;30000;00000;30000;50236;00553;00012;00008;00000;00100;\r\n
        0;10008;10010;09960;50248;00001;00000;30000;00000;30000;50240;00553;00012;00008;00000;00100;\r\n
        0;10014;10010;09960;50254;00001;00000;30000;00000;30000;50240;00553;00012;00008;00000;00100;\r\n

        Input for this class:

        header = [
        'leading_0',
        'psense_live',
        'psense_base',
        'psense_thresh',
        'psense_base_puff',
        'psense_tripped',
        'duty',
        'r_heater',
        'r_targ',
        'r_base',
        'psense_amb',
        'batt_live',
        'reset_reason',
        'lumped_acc',
        'motion_lockout_count',
        'i2c_error_count',
        ]
        delimiter = ';'
        ending = '\r\n'
        is_timestamped = False

    '''
    @dataclass
    class PlotConfig:
        want_to_plot: bool = False
        y_min: int = 0
        y_max: int = 0
        index: int = 0

    ## --------------- USER ENTRY --------------- ##
    # Enter the entire column header in order 
    # Fill in the values for columns to plot (want_to_plot, y_min, y_max)
    # Note: if timestamp is not included in the data, set is_timestamped to False
    header_config = {
        'leading_0': PlotConfig(),
        'times_tamp': PlotConfig(),
        'scale': PlotConfig(),
        'r_live': PlotConfig(True, 12000, 16000),
        'r_base': PlotConfig(True, 12000, 16000),
        'r_targ': PlotConfig(True, 12000, 16000),
        'p_live': PlotConfig(),
        'seebeck': PlotConfig(),
        'seebeck_offset': PlotConfig(),
        'seebeck_avg': PlotConfig(),
        'r_fast': PlotConfig(),
        'r_slow': PlotConfig(),
    }
    delimiter = ','
    ending = '\r\n'
    is_timestamped = False
    timestamp_key = 'timestamp'
    
    num_samples = 300                   # Number of samples to plot per frame
    stream_rate_period = 8             # [ms]

    baudrate = 115200
    port = '/dev/tty.SLAB_USBtoUART'

    title = 'Data Live Plot'
    ## ------------------------------------------ ##

    to_plot = {}
    _index = 0
    if not is_timestamped or timestamp_key not in header_config.keys():
        timestamp_dict = {timestamp_key: PlotConfig(True)}
        header_config = {**timestamp_dict, **header_config}
    for key, value in header_config.items():
        if value.want_to_plot:
            value.index = _index
            to_plot.update({key: value})
        _index += 1
    num_col = len(header_config.keys())         
    num_to_plot = len(to_plot.keys()) - 1       # Don't count timestamp

class LivePlot:
    def __init__(self):
        self.stream_config = StreamConfig()
        self.num_col = self.stream_config.num_col
        self.delimiter = self.stream_config.delimiter
        self.ending = self.stream_config.ending
        self.num_to_plot = self.stream_config.num_to_plot
        self.is_timestamped = self.stream_config.is_timestamped
        self.timestamp_key = self.stream_config.timestamp_key
        self.time_max = self.stream_config.num_samples * self.stream_config.stream_rate_period                # ms when it starts scrolling
        @dataclass
        class PlotData:
            config: Dict
            data: List
            app: Callable
        self.data = {}
        for key, value in self.stream_config.to_plot.items():
            data = []
            self.data.update({key: PlotData(config=value, data=data, app=data.append)})
        self.ax = [None] * self.num_to_plot
        self.ln = [None] * self.num_to_plot
        
        # Set Figure 
        self.set_figure()

        self.data_list = []

        self.ani = None
        self.scroll_flag = False
        self.plot_flag = False
        self.first_line = True
        self.plot_loop_flag = False

    def set_figure(self):
        # Define figure
        self.fig = plt.figure(figsize=(6,8))
        self.fig.suptitle(self.stream_config.title)

        i = 1
        for key in self.data.keys():
            if key == self.timestamp_key:
                continue
            print("{} {} {} {}".format(i, key, self.data[key].config.y_min, self.data[key].config.y_max))
            self.ax[i-1] = self.fig.add_subplot(self.num_to_plot,1,i,ylim=(self.data[key].config.y_min,self.data[key].config.y_max),xlim=(0,self.time_max))
            self.ax[i-1].set_ylabel(key)
            self.ax[i-1].get_xaxis().set_visible(False)
            self.ln[i-1] = self.ax[i-1].plot([], [], linewidth=1.5)[0]
            i += 1

    # THREAD: Parse new data to lists for plotting 
    def parse(self):
        while True:
            if len(self.data_list) > 0:
                new_line = self.data_list.pop(1)
                device_data = np.array(new_line, dtype=np.float32)
                if len(device_data) == self.stream_config.num_col:
                    if self.first_line:
                        self.first_line = False
                        self.time_start = device_data[self.data[self.timestamp_key].config.index]
                    if device_data[self.data[self.timestamp_key].config.index]-self.time_start > self.time_max:
                        self.scroll_flag = True
                        for key in self.data.keys():
                            self.data[key].data.pop(0)
                    for key in self.data.keys():
                        if key == self.timestamp_key:
                            self.data[key].app(device_data[self.data[key].config.index] - self.time_start)
                        else:
                            self.data[key].app(device_data[self.data[key].config.index])
            else:
                # continue
                time.sleep(0.0001)

    def append_line(self, new_line):
        self.data_list.append(new_line)

    def print_datalist(self):
        for i in range(len(self.data_list)):
            print(self.data_list[i])

    def clear_data(self):
        self.ani = None
        for key in self.data.keys():
            self.data[key].data.clear()

    def set_plot_flag(self,value):
        self.plot_flag = value

    # THREAD: Live plot incoming data
    def plot_loop(self):
        self.plot_flag = False
        self.fig.canvas.mpl_connect('close_event', self.close_loop)
        self.fig.canvas.draw()
        plt.show(block=False)
        while True:
            if self.plot_loop_flag: # True when stream is finished
                print("\nClose plot window to continue...")
                plt.show()
                print('Plot closed! Continue for more tests or press [Ctrl+C] to exit\n')
                self.plot_loop_flag = False
                self.scroll_flag = False
                self.first_line = True
                break
            if self.scroll_flag:    # Start scrolling
                for i in range(len(self.ax)):
                    self.ax[i].set_xlim(self.data[self.timestamp_key].data[0], self.data[self.timestamp_key].data[-1])
            i = 0
            for key in self.data.keys():
                if key == self.timestamp_key:
                    continue
                self.ln[i].set_data(self.data[self.timestamp_key].data, self.data[key].data)
                i += 1
            i = 0
            for i in range(len(self.ax)):
                self.ax[i].draw_artist(self.ax[i].patch)
                i += 1
            i = 0
            for i in range(len(self.ln)):
                self.ax[i].draw_artist(self.ln[i])
                i += 1
            self.fig.canvas.update()
            self.fig.canvas.flush_events()

    def close_loop(self,evt):
        plt.close()

class StreamMPM:
    def __init__(self, l_plot):
        self.live_plot = l_plot

        self.ser = serial.Serial(port=self.live_plot.stream_config.port, baudrate=self.live_plot.stream_config.baudrate, timeout=1)  # open serial port
        print("\nConnected to "+self.ser.port)

        self.msg = ''

        self.ani = None

        self.exit_flag = False
        self.time_start = time.time()*1000

    def readline_mod(self):
        msg = self.ser.readline().decode('utf-8')
        ending_length = len(self.live_plot.ending) + 1
        if msg[-ending_length:] == '{}{}'.format(self.live_plot.delimiter, self.live_plot.ending):
            msg = msg[:-ending_length]
        if not self.live_plot.is_timestamped:
            msg = '{}{}{}'.format(int(time.time()*1000-self.time_start), self.live_plot.delimiter, msg)
        return msg

    def stream(self):
        i = 0
        self.live_plot.set_plot_flag(True)
        while not self.exit_flag:
            try:
                self.msg = self.readline_mod()
            except (OSError, UnicodeDecodeError, serial.serialutil.SerialException):
                pass
            if self.msg.count(self.live_plot.delimiter) == self.live_plot.num_col-1:
                print(self.msg)
                content = self.msg.split(self.live_plot.delimiter)
                self.live_plot.append_line(content)
            else:
                time.sleep(0.005)

    def close(self):
        self.exit_flag = True
        self.ser.close()
        plt.close()
        print("\n\nClosing system...")
        return None


if __name__ == "__main__":
    # try:
    l_plot = LivePlot()
    stream = StreamMPM(l_plot)
    stream_thread = threading.Thread(target=stream.stream, daemon=True)
    stream_thread.setName('StreamThread')
    parse_thread = threading.Thread(target=stream.live_plot.parse, daemon=True)
    parse_thread.setName('ParseThread')
    stream_thread.start()
    parse_thread.start()
    time.sleep(0.5)

    while True:
        if l_plot.plot_flag:
            l_plot.plot_loop()
            l_plot.clear_data()
            l_plot.set_figure()
        else:
            if stream.exit_flag:
                break
            time.sleep(0.005)
    # except KeyboardInterrupt:
    #     pass
    # except Exception as e:
    #     print(str(e))
    # finally:
    l_plot.set_plot_flag(False)
    stream.close()
