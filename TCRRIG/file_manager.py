import os
from datetime import datetime as dt
import threading

LO_RES_TIME_FORMAT = '%04d%02d%02d'      # YYYYMMDD
HI_RES_TIME_FORMAT = '%04d%02d%02d-%02d%02d%02d'    #YYYYMMDD-HHMMSS
        
class FILE_MANAGER():
    def __init__(self):
        self.log_directory = 'logs/'
        self.log = ''
        self.log_file = ''
        self.lock = threading.Lock()
        self.setup_directories()

    def setup_directories(self):
        # Create main log directory
        if not os.path.isdir(self.log_directory):
            os.mkdir(self.log_directory)
        else:
            print("%s already exists!" % self.log_directory)

    def create_log_file(self):
        now = dt.now()
        self.lock.acquire()

        # Attempt to close the last logfile
        try:
            self.log.close()
        except Exception as e:
            pass
            # print("Logfile '%s' does not exist!" % self.log)
            # print("Error:", e)

        # Check if main log directory exists
        if not os.path.isdir(self.log_directory):
            self.setup_directories()
        self.log_file = (HI_RES_TIME_FORMAT % (now.year, now.month, now.day, now.hour, now.minute, now.second)) + '.log'
        
        # Open logfile and write header
        self.log = open(self.log_directory + self.log_file, "w")
        self.log.write("DATA LOG: PAX ERA LIFE\r")
        self.log.write("DATE: %04d-%02d-%02d\r" % (now.year, now.month, now.day))
        self.log.write("TIME: %02d:%02d:%02d\r\n\n" % (now.hour, now.minute, now.second))
        self.log.flush()

        self.lock.release()

        return self.log_file

    def close_log_file(self):
        self.lock.acquire()
        try:
            self.log.close()
        except Exception as e:
            self.log_file = ''
        self.lock.release()
        return self.log_file

    def write_log(self, data):
        try:
            self.lock.acquire()
            self.log.write(data + '\n')
            self.log.flush()
            self.lock.release()
        except:
            pass


file_manager = FILE_MANAGER()

