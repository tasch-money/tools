import sys, glob
from time import sleep
import time
import serial
import threading
import json
import PySimpleGUI as sg

from file_manager import file_manager as fm
from plotting import plotter
from datetime import datetime

PROJECT_TITLE = 'PAX X3/WILLOW CLI'
PROJECT_COLOR_THEME = 'Black'      # 'DarkAmber'

GUI_TEXTSIZE_TITLE = 20
GUI_TEXTSIZE_FRAME = 14
GUI_TEXTSIZE_SUBTEXT = 12

GUI_INPUTTEXT_SIZE = 12
GUI_INPUTTEXT_COLOR = '#32CD32'   # Hacker Lime
GUI_INPUTTEXT_STYLE = 'bold'
GUI_INPUTTEXT_JUSTIFY = 'right'

GUI_TEXTFONT_ALL = 'default'

GUI_FONT_MAIN = (GUI_TEXTFONT_ALL, GUI_TEXTSIZE_SUBTEXT)
GUI_FONT_FRAME = (GUI_TEXTFONT_ALL, GUI_TEXTSIZE_FRAME)
GUI_FONT_TITLE = (GUI_TEXTFONT_ALL, GUI_TEXTSIZE_TITLE)

GUI_BORDERWIDTH_FRAME = 10

cp = sg.cprint

# Define overall GUI theme color scheme (See bottom of script for possible color themes)
# sg.theme('DarkAmber')
sg.theme(PROJECT_COLOR_THEME)

PETAL_LOOKUP = {1: '270', 2: '320', 3: '370', 4: '420'}

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

def list_serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(20)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

FRAME_COMMS_LAYOUT = [
    [sg.Text('Serial Port:',size=(8,1),font=GUI_FONT_MAIN),sg.Combo(list_serial_ports(), font=GUI_FONT_MAIN, size=20, readonly=True, enable_events=True, key='gui_comms_port_list'),sg.Button('OPEN', key='gui_button_open_port'),sg.Button('CLOSE', key='gui_button_close_port')],
    [sg.Text('Status:',size=(8,1),font=GUI_FONT_MAIN),LEDIndicator(key='gui_status_comms',radius=14),sg.T('',size=(8,1),font=GUI_FONT_MAIN,key='gui_text_comms_stat'),sg.T('',size=(13,1)),sg.Button('REFRESH PORTS', key='gui_button_refresh_port')],
]

FRAME_DATA_PROCESSING_LAYOUT = [
    [sg.Text('Data File:',size=(8,1),font=GUI_FONT_MAIN),sg.Input(key='gui_process_data_file',size=(26,1),font=GUI_FONT_MAIN, change_submits=True, disabled=True),sg.FileBrowse(key='gui_process_file_browser', size=(6,1), font=GUI_FONT_MAIN),sg.Button('PLOT',key='gui_button_process_plot',size=(4,1),font=GUI_FONT_MAIN)],
    [sg.Text('Config File:',size=(8,1),font=GUI_FONT_MAIN),sg.Input(key='gui_process_config_file',size=(26,1),font=GUI_FONT_MAIN, change_submits=True, disabled=True),sg.FileBrowse(key='gui_process_config_browser', size=(6,1), font=GUI_FONT_MAIN)],
]

FRAME_HEATER_SETTINGS_LAYOUT = [
    [sg.Button('Master Streaming Toggle', key='gui_button_streaming_send',size = 22), sg.T('',size=(2,1)),sg.Button('Heater Data Toggle', key='gui_button_heater_data_send',size = 22)],
    [sg.Button('Battery Data Toggle', key='gui_button_battery_data_send',size = 22), sg.T('',size=(2,1)), sg.Button('Lip Sense Data Toggle', key='gui_button_lip_sense_data_send',size = 22)],
    [sg.Button('Suspend Heating', key='gui_button_suspend_heating_send',size = 22), sg.T('',size=(2,1)), sg.Button('Resume Heating', key='gui_button_resume_heating_send',size = 22)],

  ]

FRAME_POKE_LAYOUT = [
    [sg.Button('Enable CLI',key='gui_button_poke_command_send',font=GUI_FONT_MAIN, size=(12))],
]


FRAME_CONSOLE_LAYOUT = [
    [sg.Multiline(key='gui_cons_output',font=GUI_FONT_MAIN, text_color = 'LightGreen', autoscroll=True,size=(100,10),reroute_cprint=True, write_only=True)],
]

GUI_LAYOUT = [  
    [sg.Text(PROJECT_TITLE, font=GUI_FONT_TITLE, key='gui_title')],
    [sg.Frame('CONNECTION', FRAME_COMMS_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_serial'),sg.Frame('DATA PROCESSING', FRAME_DATA_PROCESSING_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_data_flow_ctrl')],
    [sg.Frame('HEATER SETTINGS', FRAME_HEATER_SETTINGS_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_heater_settings'),sg.Frame('POKE THE PAX',FRAME_POKE_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_button_poke_command_send')],
    [sg.Frame('CONSOLE', FRAME_CONSOLE_LAYOUT, font=GUI_FONT_FRAME, border_width=GUI_BORDERWIDTH_FRAME, key='gui_frame_console')],
    [sg.Button('EXIT', key='gui_button_exit')],
]

class SerialPort:
    def __init__(self):
        self.port = None
        self.ser = None
        self.port_new = None
        self.port_open = False
        self.lock = threading.Lock()
        self.last_command = ''
        self.send_command_flag = False
        self.resend_command_flag = False

    def open_port(self, port, baud=115200, time_out=0.1):
        self.lock.acquire()
        if self.port_open:
            if self.port != port:
                cp("PORT {} already open!".format(self.port))
                self.ser.close()
                cp("PORT {} now closed!".format(self.port))
            else:
                cp("PORT {} already open!".format(self.port))
                self.lock.release()
                return False
        else:
            if not port:
                cp("No PORT selected from menu!")
                self.lock.release()
                return False
        self.port = port
        cp("OPENING PORT: {}".format(self.port))
        try:
            self.ser = serial.Serial(port=self.port, baudrate=baud, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=time_out)
            self.port_open = True
            self.flush_port()
            self.lock.release()
            cp("PORT {} now open!".format(self.port))
            return True
        except:
            self.lock.release()
            cp("Serial Port %s is no longer available. Check connections!" % self.port)
            return False

    

    def close_port(self):
        if self.port_open:
            self.lock.acquire()
            cp("CLOSING PORT: {}".format(self.port))
            self.ser.close()
            self.port_open = False
            self.lock.release()
            cp("PORT {} now closed!".format(self.port))
            return True
        else:
            cp("No PORT actively open!")
            return False

    def flush_port(self):
        while self.ser.in_waiting:
            self.ser.read(1)

    def is_port_open(self):
        if self.port_open:
            return True
        else:
            cp('No serial port actively open! Connect to a serial port and resend.')
            return False

    def send_msg(self, msg):
        msg += '\r'
        self.ser.write(msg.encode())
        self.last_command = msg

    def resend_msg(self):
        self.ser.write(self.last_command.encode())
        self.resend_command_flag = False

    def RX(self):
        self.lock.acquire()
        try:
            line = self.ser.readline().strip().decode()
        except:
            line = ''
        self.lock.release()
        return line

class GUI(SerialPort):
    def __init__(self, gui_title, layout):
        SerialPort.__init__(self)
        self.event = ''
        self.e_val = ''
        self.layout = layout

        # Hard coded pax labs log image as base-64
        self.pax_icon_base_64 = b'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'
        sg.set_global_icon(self.pax_icon_base_64)
        self.window = sg.Window(gui_title, self.layout, icon=self.pax_icon_base_64, finalize=True, resizable=True)

        # Initialize LEDs
        SetLED(self.window, 'gui_status_comms','','red')

        # Initialze all displayed parameters
        #self.update_param('gui_heater_tcr'      ,   '-')

        self.plot_file_path = ''
        self.config_file_path = 'plot_config.json'

        #self.tx_check_box_dict = {'tcr':[1], 'temp':[1]}
        self.current_settings = {}        
        self.log_stat = 0
        self.petal = 2

        self.initialize_flag = False

    def update_param(self, param, val):
        self.window[param].Update(value=val)

    def parse_line(self, line):
        try:
            cp(line)
            if self.log_stat == 1:
                    fm.write_log(line, )
            param = ''
        except:
            cp('ERROR: BAD DATA LINE!')

    def enable_logging(self, enable):
        if enable:
            logfile = fm.create_log_file()
            cp('New logfile created: %s' % logfile)
            self.log_stat = 1
        else:
            logfile = fm.close_log_file()
            cp('Closing logfile: %s' % logfile)
            self.log_stat = 0

    def event_loop(self):
        # Event Loop to process "events"
        while True:
            self.event, self.e_val = self.window.read()
            # cp(self.event, self.e_val)
            # TIMEOUT
            if self.event == '__TIMEOUT__':
                pass

            # SERIAL COMMS
            elif self.event == 'gui_comms_port_list':
                self.port_new = self.window['gui_comms_port_list'].get()
            elif self.event == 'gui_button_open_port':
                if self.open_port(self.port_new):
                    SetLED(self.window, 'gui_status_comms','green','green')
                    self.enable_logging(1)
                    self.update_param('gui_text_comms_stat', 'OPEN')
                    self.send_msg('!!!O')
                    self.initialize_flag = True
            elif self.event == 'gui_button_close_port':
                if self.close_port():
                    SetLED(self.window, 'gui_status_comms','red','red')
                    self.enable_logging(0)
                    self.update_param('gui_text_comms_stat', 'CLOSED')

            elif self.event == 'gui_button_refresh_port':
                cp("Refreshing Serial Ports!")
                self.window['gui_comms_port_list'].Update(values=list_serial_ports())
            #elif self.event == 'gui_initialize_dvc_message':
                #if self.e_val[self.event] == 'tcr':
                    #self.send_msg('h')
               # elif self.e_val[self.event] == 'temp':
                    #self.send_msg('d')

            # DATA PROCESSING
            elif self.event == 'gui_process_data_file':
                self.plot_file_path = self.window['gui_process_data_file'].get()
            elif self.event == 'gui_process_config_file':
                self.config_file_path = self.window['gui_process_config_file'].get()
            elif self.event == 'gui_button_process_plot':
                if self.plot_file_path != '':
                    if self.config_file_path != '':
                        cp('Plotting file: %s' % self.plot_file_path.split('/')[-1])
                        cp('Configuration file: %s' % self.config_file_path.split('/')[-1])
                        cp('PLOTTING!')
                        plotter.load_config_file(self.config_file_path)
                        if plotter.load_data_file(self.plot_file_path):
                            plotter.run()
                        else:
                            cp('Bad data import of file!')
                    else:
                        cp('Please choose a configuration file!')
                else:
                    cp('Please choose a data and configuration file to plot!')

            # HEATER CONTROL
            elif self.event == 'gui_button_streaming_send':
                if self.is_port_open():
                    cp("Toggling Streaming")
                    self.send_msg('d')
            elif self.event == 'gui_button_heater_data_send':
                    cp("Toggling Heater Streaming")
                    self.send_msg('h')
            elif self.event == 'gui_button_battery_data_send':
                    cp("Toggling Battery Streaming")
                    self.send_msg('b')
            elif self.event == 'gui_button_lip_sense_data_send':
                    cp("Toggling Lip Sense Streaming")
                    self.send_msg('p')
            elif self.event == 'gui_button_suspend_heating_send':
                    cp("Suspending Heating")
                    self.send_msg('g')
            elif self.event == 'gui_button_resume_heating_send':
                    cp("Resuming Heating")
                    self.send_msg('f')

            # POKE THE PAX
            elif self.event == 'gui_button_poke_command_send':
                    cp("Poke")
                    self.send_msg('!!!O')
                    

            # ENDING
            elif self.event == sg.WIN_CLOSED or self.event == 'gui_button_exit':
                self.close_port()
                break

            sleep(0.1)
                
        self.window.close()

def thread_comms(thread_name, period, gui):
    while True:
        if gui.port_open:
            try:
                while gui.ser.in_waiting:
                    line = gui.RX()
                    gui.parse_line(line)
                if gui.resend_command_flag:
                    gui.resend_msg()
            except:
                pass
        sleep(period * 0.001)
        # window.write_event_value(thread_name, f'count = {i}')



gui = GUI(PROJECT_TITLE, GUI_LAYOUT)

threading.Thread(target=thread_comms, args=('gui_thread_comms', 10, gui), daemon=True).start()

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