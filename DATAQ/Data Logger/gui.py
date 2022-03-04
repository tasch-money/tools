import sys, glob
from time import sleep
import time
import threading
import json
import PySimpleGUI as sg

from di2008 import DI2008
from file_manager import file_manager as fm
from plotting import plotter

PROJECT_TITLE = 'DI-2008 DATA LOGGER'
PROJECT_COLOR_THEME = 'Purple'      # 'DarkAmber'

NUM_TC_CHANNELS = 8

GUI_TEXTSIZE_TITLE = 20
GUI_TEXTSIZE_FRAME = 14
GUI_TEXTSIZE_SUBTEXT = 12

GUI_INPUTTEXT_SIZE = 12
GUI_INPUTTEXT_COLOR = '#008B8B'   # Dark Teal
GUI_INPUTTEXT_STYLE = 'bold'
GUI_INPUTTEXT_JUSTIFY = 'right'

GUI_TEXTFONT_ALL = 'default'

GUI_FONT_MAIN = (GUI_TEXTFONT_ALL, GUI_TEXTSIZE_SUBTEXT)
GUI_FONT_FRAME = (GUI_TEXTFONT_ALL, GUI_TEXTSIZE_FRAME)
GUI_FONT_TITLE = (GUI_TEXTFONT_ALL, GUI_TEXTSIZE_TITLE)

GUI_BORDERWIDTH_FRAME = 10

PARSE_LINE_PARAM_UPDATE_LIST = ['tcr', 'temp']
cp = sg.cprint

# Define overall GUI theme color scheme (See bottom of script for possible color themes)
# sg.theme('DarkAmber')
sg.theme(PROJECT_COLOR_THEME)

# Global Functions
def LEDIndicator(key=None, radius=15):
    return sg.Graph(canvas_size=(radius, radius),
             graph_bottom_left=(-radius, -radius),
             graph_top_right=(radius, radius),
             pad=(0, 0), key=key)

def SetLED(window, key, fcolor, lcolor):
    graph = window[key]
    graph.erase()
    graph.draw_circle((0, 0), 12, fill_color=fcolor, line_color=lcolor)


FRAME_CONNECTION_LAYOUT = [
    [sg.Button('CONNECT', font=GUI_FONT_MAIN, size=(12,1), key='gui_button_connect'),sg.Button('DISCONNECT', font=GUI_FONT_MAIN, size=(12,1), key='gui_button_disconnect')],
    [sg.Text('Status:',size=(8,1),font=GUI_FONT_MAIN),LEDIndicator(key='gui_status_comms',radius=14),sg.T('',size=(8,1),font=GUI_FONT_MAIN,key='gui_text_comms_stat')],
]

FRAME_DATA_PROCESSING_LAYOUT = [
    [sg.Text('Data File:',size=(8,1),font=GUI_FONT_MAIN),sg.Input(key='gui_process_data_file',size=(26,1),font=GUI_FONT_MAIN, change_submits=True, disabled=True),sg.FileBrowse(key='gui_process_file_browser', size=(6,1), font=GUI_FONT_MAIN),sg.Button('PLOT',key='gui_button_process_plot',size=(4,1),font=GUI_FONT_MAIN)],
    [sg.T('', size=(1,1))],
]

FRAME_SAMPLE_RATE_LAYOUT = [
    [sg.Combo([0.2, 1, 10, 20, 25], default_value=10, font=GUI_FONT_MAIN, size=6, readonly=True, enable_events=True, key='gui_sample_rate_list'), sg.Text('Hz', font=GUI_FONT_MAIN, size=2)],
    [sg.T('', size=1)]
]

FRAME_CHANNEL1_LAYOUT = [
    [LEDIndicator(key='gui_status_channel1',radius=14), sg.Button('ON', size=(8,1), key='gui_button_on1'),sg.Button('OFF', size=(8,1), key='gui_button_off1')],
    [sg.Text('TYPE:',size=(6,1),font=GUI_FONT_MAIN), sg.Combo(['B', 'E', 'J', 'K', 'N', 'R', 'S', 'T'], default_value='K', font=GUI_FONT_MAIN, size=8, readonly=True, enable_events=True, key='gui_tc_type_list1')], 
    [sg.Text('TEMPERATURE',size=(12,1),font=GUI_FONT_MAIN)],
    [sg.Input(key='gui_temp_display1', disabled=True, size=(16,1), font=(GUI_TEXTFONT_ALL, GUI_INPUTTEXT_SIZE, GUI_INPUTTEXT_STYLE), justification=GUI_INPUTTEXT_JUSTIFY)]
]

FRAME_CHANNEL2_LAYOUT = [
    [LEDIndicator(key='gui_status_channel2',radius=14), sg.Button('ON', size=(8,1), key='gui_button_on2'),sg.Button('OFF', size=(8,1), key='gui_button_off2')],
    [sg.Text('TYPE:',size=(6,1),font=GUI_FONT_MAIN), sg.Combo(['B', 'E', 'J', 'K', 'N', 'R', 'S', 'T'], default_value='K', font=GUI_FONT_MAIN, size=8, readonly=True, enable_events=True, key='gui_tc_type_list2')], 
    [sg.Text('TEMPERATURE',size=(12,1),font=GUI_FONT_MAIN)],
    [sg.Input(key='gui_temp_display2', disabled=True, size=(16,1), font=(GUI_TEXTFONT_ALL, GUI_INPUTTEXT_SIZE, GUI_INPUTTEXT_STYLE), justification=GUI_INPUTTEXT_JUSTIFY)]
]

FRAME_CHANNEL3_LAYOUT = [
    [LEDIndicator(key='gui_status_channel3',radius=14), sg.Button('ON', size=(8,1), key='gui_button_on3'),sg.Button('OFF', size=(8,1), key='gui_button_off3')],
    [sg.Text('TYPE:',size=(6,1),font=GUI_FONT_MAIN), sg.Combo(['B', 'E', 'J', 'K', 'N', 'R', 'S', 'T'], default_value='K', font=GUI_FONT_MAIN, size=8, readonly=True, enable_events=True, key='gui_tc_type_list3')], 
    [sg.Text('TEMPERATURE',size=(12,1),font=GUI_FONT_MAIN)],
    [sg.Input(key='gui_temp_display3', disabled=True, size=(16,1), font=(GUI_TEXTFONT_ALL, GUI_INPUTTEXT_SIZE, GUI_INPUTTEXT_STYLE), justification=GUI_INPUTTEXT_JUSTIFY)]
]

FRAME_CHANNEL4_LAYOUT = [
    [LEDIndicator(key='gui_status_channel4',radius=14), sg.Button('ON', size=(8,1), key='gui_button_on4'),sg.Button('OFF', size=(8,1), key='gui_button_off4')],
    [sg.Text('TYPE:',size=(6,1),font=GUI_FONT_MAIN), sg.Combo(['B', 'E', 'J', 'K', 'N', 'R', 'S', 'T'], default_value='K', font=GUI_FONT_MAIN, size=8, readonly=True, enable_events=True, key='gui_tc_type_list4')], 
    [sg.Text('TEMPERATURE',size=(12,1),font=GUI_FONT_MAIN)],
    [sg.Input(key='gui_temp_display4', disabled=True, size=(16,1), font=(GUI_TEXTFONT_ALL, GUI_INPUTTEXT_SIZE, GUI_INPUTTEXT_STYLE), justification=GUI_INPUTTEXT_JUSTIFY)]
]

FRAME_CHANNEL5_LAYOUT = [
    [LEDIndicator(key='gui_status_channel5',radius=14), sg.Button('ON', size=(8,1), key='gui_button_on5'),sg.Button('OFF', size=(8,1), key='gui_button_off5')],
    [sg.Text('TYPE:',size=(6,1),font=GUI_FONT_MAIN), sg.Combo(['B', 'E', 'J', 'K', 'N', 'R', 'S', 'T'], default_value='K', font=GUI_FONT_MAIN, size=8, readonly=True, enable_events=True, key='gui_tc_type_list5')], 
    [sg.Text('TEMPERATURE',size=(12,1),font=GUI_FONT_MAIN)],
    [sg.Input(key='gui_temp_display5', disabled=True, size=(16,1), font=(GUI_TEXTFONT_ALL, GUI_INPUTTEXT_SIZE, GUI_INPUTTEXT_STYLE), justification=GUI_INPUTTEXT_JUSTIFY)]
]

FRAME_CHANNEL6_LAYOUT = [
    [LEDIndicator(key='gui_status_channel6',radius=14), sg.Button('ON', size=(8,1), key='gui_button_on6'),sg.Button('OFF', size=(8,1), key='gui_button_off6')],
    [sg.Text('TYPE:',size=(6,1),font=GUI_FONT_MAIN), sg.Combo(['B', 'E', 'J', 'K', 'N', 'R', 'S', 'T'], default_value='K', font=GUI_FONT_MAIN, size=8, readonly=True, enable_events=True, key='gui_tc_type_list6')], 
    [sg.Text('TEMPERATURE',size=(12,1),font=GUI_FONT_MAIN)],
    [sg.Input(key='gui_temp_display6', disabled=True, size=(16,1), font=(GUI_TEXTFONT_ALL, GUI_INPUTTEXT_SIZE, GUI_INPUTTEXT_STYLE), justification=GUI_INPUTTEXT_JUSTIFY)]
]

FRAME_CHANNEL7_LAYOUT = [
    [LEDIndicator(key='gui_status_channel7',radius=14), sg.Button('ON', size=(8,1), key='gui_button_on7'),sg.Button('OFF', size=(8,1), key='gui_button_off7')],
    [sg.Text('TYPE:',size=(6,1),font=GUI_FONT_MAIN), sg.Combo(['B', 'E', 'J', 'K', 'N', 'R', 'S', 'T'], default_value='K', font=GUI_FONT_MAIN, size=8, readonly=True, enable_events=True, key='gui_tc_type_list7')], 
    [sg.Text('TEMPERATURE',size=(12,1),font=GUI_FONT_MAIN)],
    [sg.Input(key='gui_temp_display7', disabled=True, size=(16,1), font=(GUI_TEXTFONT_ALL, GUI_INPUTTEXT_SIZE, GUI_INPUTTEXT_STYLE), justification=GUI_INPUTTEXT_JUSTIFY)]
]

FRAME_CHANNEL8_LAYOUT = [
    [LEDIndicator(key='gui_status_channel8',radius=14), sg.Button('ON', size=(8,1), key='gui_button_on8'),sg.Button('OFF', size=(8,1), key='gui_button_off8')],
    [sg.Text('TYPE:',size=(6,1),font=GUI_FONT_MAIN), sg.Combo(['B', 'E', 'J', 'K', 'N', 'R', 'S', 'T'], default_value='K', font=GUI_FONT_MAIN, size=8, readonly=True, enable_events=True, key='gui_tc_type_list8')], 
    [sg.Text('TEMPERATURE',size=(12,1),font=GUI_FONT_MAIN)],
    [sg.Input(key='gui_temp_display8', disabled=True, size=(16,1), font=(GUI_TEXTFONT_ALL, GUI_INPUTTEXT_SIZE, GUI_INPUTTEXT_STYLE), justification=GUI_INPUTTEXT_JUSTIFY)]
]

GUI_LAYOUT = [  
    [sg.Text(PROJECT_TITLE, font=GUI_FONT_TITLE, key='gui_title')],
    [sg.Frame('CONNECTION', FRAME_CONNECTION_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_connection'), sg.Frame('SAMPLE RATE', FRAME_SAMPLE_RATE_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_sample_rate'), sg.Frame('DATA PROCESSING', FRAME_DATA_PROCESSING_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_data_flow_ctrl')],
    [sg.Frame('CHANNEL 1', FRAME_CHANNEL1_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_channel1'), sg.Frame('CHANNEL 2', FRAME_CHANNEL2_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_channel2'),
     sg.Frame('CHANNEL 3', FRAME_CHANNEL3_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_channel3'), sg.Frame('CHANNEL 4', FRAME_CHANNEL4_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_channel4'),
     sg.Frame('CHANNEL 5', FRAME_CHANNEL5_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_channel5'), sg.Frame('CHANNEL 6', FRAME_CHANNEL6_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_channel6'),
     sg.Frame('CHANNEL 7', FRAME_CHANNEL7_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_channel7'), sg.Frame('CHANNEL 8', FRAME_CHANNEL8_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_channel8')],
    [sg.Button('START', size=8, key='gui_button_start'), sg.Button('STOP', size=8, key='gui_button_stop'), sg.Button('EXIT', key='gui_button_exit')],
]

class GUI():
    def __init__(self, gui_title, layout, dvc):
        self.event = ''
        self.e_val = ''
        self.layout = layout
        self.tc_dvc = dvc

        # Hard coded pax labs log image as base-64
        self.pax_icon_base_64 = b'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'
        sg.set_global_icon(self.pax_icon_base_64)
        self.window = sg.Window(gui_title, self.layout, icon=self.pax_icon_base_64, finalize=True, resizable=True)

        # Initialize LEDs
        SetLED(self.window, 'gui_status_comms','','red')
        SetLED(self.window, 'gui_status_channel1','green','green')
        SetLED(self.window, 'gui_status_channel2','green','green')
        SetLED(self.window, 'gui_status_channel3','green','green')
        SetLED(self.window, 'gui_status_channel4','green','green')
        SetLED(self.window, 'gui_status_channel5','green','green')
        SetLED(self.window, 'gui_status_channel6','green','green')
        SetLED(self.window, 'gui_status_channel7','green','green')
        SetLED(self.window, 'gui_status_channel8','green','green')


        # Initialze all displayed parameters
        self.update_param('gui_temp_display1'      ,   '-')
        self.update_param('gui_temp_display2'      ,   '-')
        self.update_param('gui_temp_display3'      ,   '-')
        self.update_param('gui_temp_display4'      ,   '-')
        self.update_param('gui_temp_display5'      ,   '-')
        self.update_param('gui_temp_display6'      ,   '-')
        self.update_param('gui_temp_display7'      ,   '-')
        self.update_param('gui_temp_display8'      ,   '-')

        self.plot_file_path = ''
        self.config_file_path = 'plot_config.json'

        self.log_stat = 0

        self.chan_enabled = [True] * NUM_TC_CHANNELS

    def update_param(self, param, val):
        self.window[param].Update(value=val)

    def enable_logging(self, enable):
        if enable:
            logfile = fm.create_log_file()
            print('New logfile created: %s' % logfile)
            self.log_stat = 1
            self.tc_dvc.log_enable(self.log_stat)
        else:
            logfile = fm.close_log_file()
            print('Closing logfile: %s' % logfile)
            self.log_stat = 0
            self.tc_dvc.log_enable(self.log_stat)

    def event_loop(self):
        # Event Loop to process "events"
        while True:
            self.event, self.e_val = self.window.read(timeout=1000)
            # print(self.event, self.e_val)
            # TIMEOUT
            if self.event == '__TIMEOUT__':
                for i in range(NUM_TC_CHANNELS):
                    if self.chan_enabled[i]:
                        param = 'gui_temp_display%d' % (i+1)
                        self.update_param(param, round(self.tc_dvc.temp_filt[i].result, 1))

            # CONNECTION
            elif self.event == 'gui_button_connect':
                if self.tc_dvc.discovery() == True:
                    self.tc_dvc.initialize()
                    SetLED(self.window, 'gui_status_comms','green','green')
            elif self.event == 'gui_button_disconnect':
                if self.tc_dvc.unit_connected:
                    self.tc_dvc.disconnect()
                    SetLED(self.window, 'gui_status_comms','red','red')

            # CHANNELS
            elif 'gui_button_on' in self.event:
                ch = self.event[-1]
                key = 'gui_status_channel' + ch
                self.chan_enabled[int(ch) - 1] = True
                SetLED(self.window, key,'green','green')
            elif 'gui_button_off' in self.event:
                ch = self.event[-1]
                key = 'gui_status_channel' + ch
                self.chan_enabled[int(ch) - 1] = False
                SetLED(self.window, key,'red','red')


            # DATA PROCESSING
            elif self.event == 'gui_process_data_file':
                self.plot_file_path = self.window['gui_process_data_file'].get()
            # elif self.event == 'gui_process_config_file':
            #     self.config_file_path = self.window['gui_process_config_file'].get()
            elif self.event == 'gui_button_process_plot':
                if self.plot_file_path != '':
                    if self.config_file_path != '':
                        print('Plotting file: %s' % self.plot_file_path.split('/')[-1])
                        print('Configuration file: %s' % self.config_file_path.split('/')[-1])
                        print('PLOTTING!')
                        plotter.load_config_file(self.config_file_path)
                        if plotter.load_data_file(self.plot_file_path):
                            plotter.run()
                        else:
                            print('Bad data import of file!')
                    else:
                        print('Please choose a configuration file!')
                else:
                    print('Please choose a data and configuration file to plot!')


            # START TC DATA STREAM
            elif self.event == 'gui_button_start':
                self.tc_dvc.reset_slist()
                for i in range(NUM_TC_CHANNELS):
                    if self.chan_enabled[i]:
                        key = 'gui_tc_type_list%d' % (i+1)
                        tc_type = self.e_val[key]
                        if tc_type == '':
                            self.chan_enabled[i] = False
                            SetLED(self.window, 'gui_status_channel%d' % (i+1),'red','red')
                        else:
                            self.tc_dvc.set_slist_item(i, tc_type)
                if len(self.tc_dvc.slist) > 0:
                    self.tc_dvc.begin(self.e_val['gui_sample_rate_list'])
                    self.log_stat = 1
                    self.enable_logging(self.log_stat)
                else:
                    print('No channels enabled!')

            # STOP TC DATA STREAM
            elif self.event == 'gui_button_stop':
                if self.log_stat:
                    self.log_stat = 0
                    self.enable_logging(self.log_stat)
                self.tc_dvc.stop()

            # ENDING
            elif self.event == sg.WIN_CLOSED or self.event == 'gui_button_exit':
                if self.log_stat:
                    self.log_stat = 0
                    self.enable_logging(self.log_stat)
                if self.tc_dvc.unit_connected:
                    self.tc_dvc.disconnect()
                    SetLED(self.window, 'gui_status_comms','red','red')
                break

            sleep(0.1)
                
        self.window.close()

gui = GUI(PROJECT_TITLE, GUI_LAYOUT, DI2008())

threading.Thread(target=gui.tc_dvc.run, daemon=True).start()
# threading.Thread(target=thread_acquire, args=(tc_logger, gui), daemon=True).start()

# Run main event loop
gui.event_loop()




# Possible themes to choose for GUI
# ‘Black’, ‘BlueMono’, ‘BluePurple’, ‘BrightColors’, ‘BrownBlue’, ‘Dark’, ‘Dark2’, ‘DarkAmber’, ‘DarkBlack’, ‘DarkBlack1’, 
# ‘DarkBlue’, ‘DarkBlue1’, ‘DarkBlue10’, ‘DarkBlue11’, ‘DarkBlue12’, ‘DarkBlue13’, ‘DarkBlue14’, ‘DarkBlue15’, ‘DarkBlue16’, ‘DarkBlue17’, ‘DarkBlue2’, ‘DarkBlue3’, ‘DarkBlue4’, ‘DarkBlue5’, ‘DarkBlue6’, ‘DarkBlue7’, ‘DarkBlue8’, ‘DarkBlue9’, 
# ‘DarkBrown’, ‘DarkBrown1’, ‘DarkBrown2’, ‘DarkBrown3’, ‘DarkBrown4’, ‘DarkBrown5’, ‘DarkBrown6’, 
# ‘DarkGreen’, ‘DarkGreen1’, ‘DarkGreen2’, ‘DarkGreen3’, ‘DarkGreen4’, ‘DarkGreen5’, ‘DarkGreen6’, 
# ‘DarkGrey’, ‘DarkGrey1’, ‘DarkGrey2’, ‘DarkGrey3’, ‘DarkGrey4’, ‘DarkGrey5’, ‘DarkGrey6’, ‘DarkGrey7’, 
# ‘DarkPurple’, ‘DarkPurple1’, ‘DarkPurple2’, ‘DarkPurple3’, ‘DarkPurple4’, ‘DarkPurple5’, ‘DarkPurple6’, 
# ‘DarkRed’, ‘DarkRed1’, ‘DarkRed2’, ‘DarkTanBlue’, 
# ‘DarkTeal’, ‘DarkTeal1’, ‘DarkTeal10’, ‘DarkTeal11’, ‘DarkTeal12’, ‘DarkTeal2’, ‘DarkTeal3’, ‘DarkTeal4’, ‘DarkTeal5’, ‘DarkTeal6’, ‘DarkTeal7’, ‘DarkTeal8’, ‘DarkTeal9’, 
# ‘Default’, ‘Default1’, ‘DefaultNoMoreNagging’, 
# ‘Green’, ‘GreenMono’, ‘GreenTan’, 
# ‘HotDogStand’, ‘Kayak’, ‘Reddit’, ‘Reds’, ‘SandyBeach’,
# ‘LightBlue’, ‘LightBlue1’, ‘LightBlue2’, ‘LightBlue3’, ‘LightBlue4’, ‘LightBlue5’, ‘LightBlue6’, ‘LightBlue7’, 
# ‘LightBrown’, ‘LightBrown1’, ‘LightBrown10’, ‘LightBrown11’, ‘LightBrown12’, ‘LightBrown13’, ‘LightBrown2’, ‘LightBrown3’, ‘LightBrown4’, ‘LightBrown5’, ‘LightBrown6’, ‘LightBrown7’, ‘LightBrown8’, ‘LightBrown9’, 
# ‘LightGray1’, 
# ‘LightGreen’, ‘LightGreen1’, ‘LightGreen10’, ‘LightGreen2’, ‘LightGreen3’, ‘LightGreen4’, ‘LightGreen5’, ‘LightGreen6’, ‘LightGreen7’, ‘LightGreen8’, ‘LightGreen9’, 
# ‘LightGrey’, ‘LightGrey1’, ‘LightGrey2’, ‘LightGrey3’, ‘LightGrey4’, ‘LightGrey5’, ‘LightGrey6’, 
# ‘LightPurple’, 
# ‘LightTeal’, 
# ‘LightYellow’, 
# ‘Material1’, ‘Material2’, 
# ‘NeutralBlue’, 
# ‘Purple’, 
# ‘SystemDefault’, ‘SystemDefault1’, ‘SystemDefaultForReal’, 
# ‘Tan’, ‘TanBlue’, 
# ‘TealMono’, ‘Topanga’