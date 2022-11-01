"""
    COPYRIGHT © 2018 BY DATAQ INSTRUMENTS, INC.
!!!!!!!!    VERY IMPORTANT    !!!!!!!!
!!!!!!!!    READ THIS FIRST   !!!!!!!!
This program works only with model:
DI-2008
Any other instrument model should be disconnected from the PC
to prevent the program from detecting a device with a DATAQ
Instruments VID and attempting to use it. 
Such attempts will fail.
The DI-2008 MUST be placed in its CDC communication mode. 
Follow this link for guidance:
https://www.dataq.com/blog/data-acquisition/usb-daq-products-support-libusb-cdc/
The instrument's protocol document, referred to often throughout, can be found here:
https://www.dataq.com/resources/pdfs/misc/di-2008%20protocol.pdf
"""


import serial
import serial.tools.list_ports
import time
from file_manager import file_manager as fm
import threading

"""
Change slist tuple to vary analog channel configuration.
Refer to the protocol for details.
"""
# slist = [0x1300, 0x1307]
""" slist Tuple Example Interpretation (from protocol)
0x0A00 = Channel 0, ±10 V range
0x0B01 = Channel 1, ±5 V range
0x1702 = Channel 2, T-type TC
0x1303 = Channel 3. K-type TC
0x0709 = Rate channel, 500 Hz range
0x000A = Count channel
0x0008 = Digital inputs
Define analog_ranges tuple to contain an ordered list of analog measurement ranges supported by the DI-2008. 
This tuple begins with gain code 0 (±500 mV) and ends gain code 0xD (±1 V) and is padded with 0 values
as place holders for undefined codes (see protocol.)
"""
ANALOG_RANGES   = [.5, 0.25, 0.1, .05, .025, .01, 0, 0, 50 ,25, 10, 5, 2.5, 1, 0, 0]

"""
Define a tuple that contains an ordered list of rate measurement ranges supported by the DI-2008. 
The first item in the list is the lowest gain code (e.g. 50 kHz range = gain code 1).
"""
RATE_RANGES     = tuple((50000,20000,10000,5000,2000,1000,500,200,100,50,20,10))

"""
m and b TC scaling constants in TC type order: B, E, J, K, N, R, S, T
See protocol
"""
TC_SLOPE        = [0.023956,0.018311,0.021515,0.023987,0.022888,0.02774,0.02774,0.009155]
TC_OFFSET       = [1035,400,495,586,550,859,859,100]


"""
Define a list of analog voltage and rate ranges to apply in slist order.
Value 0 is appended as a placeholder for enabled TC and dig-in channels. 
This list is populated in the config_scn_lst() routine based upon 
slist contents.
"""
# range_table = list(())

AMBIENT_TEMP = 23

TC_TYPE_LOOKUP  = {'B': 0x1000, 'E': 0x1100, 'J': 0x1200, 'K': 0x1300, 'N': 0x1400, 'R': 0x1500, 'S': 0x1600, 'T': 0x1700}

# samp_rate_hz = 100 / (int(SRATE) * int(DEC))

# Dictionary stored as {Hz: [srate, dec]}
SAMP_RATE_LOOKUP = {0.2: ['50','10'], 1: ['10','10'], 10: ['10','1'], 20: ['5','1'], 25: ['1','1']}

class DI2008():
    def __init__(self):
        self.ser = serial.Serial()
        self.unit_connected = False
        self.acquiring = False
        self.slist = []
        self.range_table = []
        self.slist_pointer = 0
        self.temperature = [0] * len(TC_SLOPE)
        self.temp_filt = [FILTER() for i in range(len(TC_SLOPE))]
        self.output_string = ''
        self.t_now = 0
        self.t_last = 0
        self.t_diff = 0
        self.log_stat = False
        self.ser_lock = threading.Lock()
        self.output_lock = threading.Lock()

    # Discover DATAQ Instruments devices and models.  Note that if multiple devices are connected, only the 
    # device discovered first is used. We leave it to you to ensure that the device is a model DI-2008
    def discovery(self):
        # Get a list of active com ports to scan for possible DATAQ Instruments devices
        available_ports = list(serial.tools.list_ports.comports())
        # Will eventually hold the com port of the detected device, if any
        hooked_port = "" 
        for p in available_ports:
            # Do we have a DATAQ Instruments device?
            if ("VID:PID=0683" in p.hwid):
                # Yes!  Dectect and assign the hooked com port
                hooked_port = p.device
                break

        self.ser_lock.acquire()
        if hooked_port:
            print("Found DATAQ Instruments device on",hooked_port)
            self.ser.timeout = 0
            self.ser.port = hooked_port
            self.ser.baudrate = '115200'
            self.ser.open()
            self.unit_connected = True
        else:
            # Get here if no DATAQ Instruments devices are detected
            print("No DATAQ Instruments device detected! Connect a device and press CONNECT!")
            self.unit_connected = False

        self.ser_lock.release()

        return self.unit_connected

    def disconnect(self):
        if self.unit_connected:
            self.ser_lock.acquire()
            self.stop()
            self.ser.close()
            self.ser_lock.release()

    def initialize(self):
        if self.unit_connected:
            # Stop in case Device was left running
            self.send_cmd("stop")
            # Keep the packet size small for responsiveness
            self.send_cmd("ps 0")

            print("")
            print("Unit initialized! Enable channels and begin...")
            print ("")
        else:
            print("Cannot call functions without unit being connected!")

    def set_sample_rate(self, sample_rate):
        if self.unit_connected:
            self.send_cmd("srate " + SAMP_RATE_LOOKUP[sample_rate][0])
            self.send_cmd("dec " + SAMP_RATE_LOOKUP[sample_rate][1])
        else:
            print("No DATAQ Instruments device detected! Connect a device and press CONNECT!")

    def reset_slist(self):
        self.slist = []

    def set_slist_item(self, channel, tc_type):
        self.slist.append(TC_TYPE_LOOKUP[tc_type] | channel)

    # Sends a passed command string after appending <cr>
    def send_cmd(self, command):
        if self.unit_connected:
            self.ser_lock.acquire()
            self.ser.write((command + '\r').encode())
            time.sleep(.1)
            if not self.acquiring:
                # Echo commands if not acquiring
                while True:
                    if (self.ser.inWaiting() > 0):
                        while True:
                            try:
                                s = self.ser.readline().decode()
                                s = s.strip('\n')
                                s = s.strip('\r')
                                s = s.strip(chr(0))
                                break
                            except:
                                continue
                        if s != "":
                            print(s)
                            break
            self.ser_lock.release()
        else:
            print("Cannot call functions without unit being connected!")

    # Configure the instrment's scan list
    def config_scn_lst(self):
        if self.unit_connected:
            # Scan list position must start with 0 and increment sequentially
            position = 0 
            for item in self.slist:
                self.send_cmd("slist "+ str(position) + " " + str(item))
                position += 1
                # Update the Range table
                if (item & 0xf < 8) and (item & 0x1000 == 0):
                    # This is a voltage channel.
                    self.range_table.append(ANALOG_RANGES[item >> 8])

                elif (item & 0xf < 8) and (item & 0x1000 != 0):
                    # This is a TC channel. Append 0 as a placeholder
                    self.range_table.append(0)

                elif item & 0xf == 8:
                    # This is a dig in channel. No measurement range support. 
                    # Append 0 as a placeholder
                    self.range_table.append(0) 

                elif item & 0xf == 9:
                    """
                    This is a rate channel
                    Rate ranges begin with 1, so subtract 1 to maintain zero-based index
                    in the rate_ranges tuple
                    """
                    self.range_table.append(RATE_RANGES[(item >> 8)-1]) 

                else:
                    """
                    This is a count channel. No measurement range support. 
                    Append 0 as a placeholder
                    """
                    self.range_table.append(0)
        else:
            print("Cannot call functions without unit being connected!")

    def begin(self, sample_rate):
        if self.unit_connected:
            self.set_sample_rate(sample_rate)
            self.config_scn_lst()
            self.acquiring = True
            time.sleep(0.5)
            self.send_cmd("start")
            self.t_now = time.time()
            self.t_last = self.t_now
        else:
            print("Unit must be connected before starting test!")

    def stop(self):
        self.send_cmd("stop")
        time.sleep(1)
        #ser.flushInput()
        print ("")
        print ("stopped")
        self.ser.flushInput()
        self.acquiring = False

    def log_enable(self, en):
        self.log_stat = en

    def get_output(self):
        self.output_lock.acquire()
        rtn_str = self.output_string
        self.output_lock.release()
        return rtn_str

    def run(self, period):
        while True:
            if self.acquiring:
                self.ser_lock.acquire()
                if self.ser.inWaiting():
                    self.output_lock.acquire()
                    self.t_now = time.time()
                    self.t_diff = self.t_now - self.t_last
                    self.t_last = self.t_now
                    self.output_string = "%f," % self.t_diff
                    while self.ser.inWaiting():   # (2 * len(self.slist))
                        for i in range(len(self.slist)):
                            # The four LSBs of slist determine measurement function
                            function = self.slist[self.slist_pointer] & 0xf
                            mode_bit = self.slist[self.slist_pointer] & 0x1000
                            # Always two bytes per sample...read them
                            if self.ser.inWaiting() >= 2:
                                new_bytes = self.ser.read(2)
                            else:
                                break
                            if (function < 8) and (not(mode_bit)):
                                # Working with a Voltage input channel. Scale accordingly.
                                result = self.range_table[self.slist_pointer] * int.from_bytes(new_bytes, byteorder='little', signed=True) / 32768
                                self.output_string = self.output_string + "{: 3.3f}, ".format(result)
                            elif (function < 8) and (mode_bit):
                                """
                                Working with a TC channel.
                                Convert to temperature if no errors.
                                First, test for TC error conditions.
                                """
                                result = int.from_bytes(new_bytes, byteorder='little', signed=True)
                                if result == 32767:
                                    print('CJC Error!')
                                # elif result == -32768:
                                #     print('OPEN Circuit!')
                                else:
                                    # Get here if no errors, so isolate TC type
                                    tc_type = self.slist[self.slist_pointer] & 0x0700
                                    tc_chan = self.slist[self.slist_pointer] & 0x000F
                                    # Move TC type into 3 LSBs to form an index we'll use to select m & b scaling constants
                                    tc_type = tc_type >> 8
                                    self.temperature[tc_chan] = TC_SLOPE[tc_type] * result + TC_OFFSET[tc_type]
                                    self.temp_filt[tc_chan].moving_avg(self.temperature[tc_chan])
                                    self.output_string = self.output_string + "{: 3.3f},{: 3.3f},".format(self.temperature[tc_chan], self.temp_filt[tc_chan].result)

                            elif function == 8:
                                # Working with the Digital input channel 
                                result = (int.from_bytes(new_bytes, byteorder='big', signed=False)) & (0x007f)
                                self.output_string = self.output_string + "{: 3d}, ".format(result)

                            elif function == 9:
                                # Working with the Rate input channel
                                result = (int.from_bytes(new_bytes, byteorder='little', signed=True) + 32768) / 65535 * (self.range_table[self.slist_pointer])
                                self.output_string = self.output_string + "{: 3.1f}, ".format(result)

                            else:
                                # Working with the Counter input channel
                                result = (int.from_bytes(new_bytes, byteorder='little', signed=True)) + 32768
                                self.output_string = self.output_string + "{: 1d}, ".format(result)

                            # Get the next position in slist
                            self.slist_pointer += 1

                            if (self.slist_pointer + 1) > (len(self.slist)):
                                # End of a pass through slist items...output, reset, continue
                                # print(self.output_string.rstrip(", ")) 
                                # self.output_string = ""
                                self.slist_pointer = 0
                    if self.log_stat:
                        fm.write_log(self.output_string.rstrip(","))
                    # print(self.output_string.rstrip(", "))

                    self.output_lock.release()
                self.ser_lock.release()

            time.sleep(period * 0.001)

FILTER_BUFF_SIZE = 32

class FILTER:
    def __init__(self):
        self.sum = AMBIENT_TEMP * FILTER_BUFF_SIZE
        self.idx = 0
        self.buffer = [AMBIENT_TEMP] * FILTER_BUFF_SIZE
        self.result = 0

    def moving_avg(self, val):
        self.sum = self.sum + val - self.buffer[self.idx]
        self.buffer[self.idx] = val
        self.idx += 1
        self.idx &= (FILTER_BUFF_SIZE - 1)
        self.result = self.sum / FILTER_BUFF_SIZE

