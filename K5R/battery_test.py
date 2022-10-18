import os
from datetime import datetime as dt
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use("TkAgg")

LO_RES_TIME_FORMAT = '%04d%02d%02d'      # YYYYMMDD
HI_RES_TIME_FORMAT = '%04d%02d%02d-%02d%02d%02d'    #YYYYMMDD-HHMMSS

log_directory = '/Users/matt/Documents/Git/tools/K5R/logs/'

column_names = [
    'dut_ts',
    'heating',
    'vbat_loaded',
    'vbat_unloaded',
    'p_live',
    'p_desired'
]

file_list = os.listdir(log_directory)
file_list.sort()

def run_df_calcs():
    t_start  = df['dut_ts'][0]
    df['timestamp'] = (df['dut_ts'] - t_start) * 1e-3
    df['100%'] = 4350
    df['75%'] = 4050
    df['50%'] = 3750
    df['25%'] = 3525
    df['5%'] = 3375


fig, ax = plt.subplots(2, sharex=True)
fig.suptitle('Raw Data')

count = 0
for file in file_list:
    if file.endswith('.log'):
        count += 1
        print("%d: %s" % (count, file))
        df = pd.DataFrame()
        df_data_lines = []
        file_path = log_directory + file
        f = open(file_path, 'r')
        r_lines = f.readlines()[4:]

        for i in range(len(r_lines)):
            temp_line = r_lines[i].split(',')

            if (temp_line[0] == '$') and (len(temp_line) == (len(column_names) + 1)):
                try:
                    temp_line.pop(0)    # Remove '$'
                    temp_list = [float(j) for j in temp_line]
                    df_data_lines.append(temp_list)
                except:
                    pass
        f.close()
        df = pd.DataFrame(df_data_lines, columns=column_names)
        df = df.dropna()
        run_df_calcs()

        x = df['timestamp']
        x_label = 'Time (sec)'
        y1 = df['vbat_unloaded']
        y2 = df['vbat_loaded']
        y_label = 'Voltage (mV)'

        fname = file.strip('.log')

        if 'd1' in fname:
            ax[0].plot(x, y1, '-',linewidth=1.0, color='blue', label=fname)
            ax[1].plot(x, y2, '-',linewidth=1.0, color='blue', label=fname)
        elif 'd2' in fname:
            ax[0].plot(x, y1, '-',linewidth=1.0, color='green', label=fname)
            ax[1].plot(x, y2, '-',linewidth=1.0, color='green', label=fname)
        elif 'd3' in fname:
            ax[0].plot(x, y1, '-',linewidth=1.0, color='yellow', label=fname)
            ax[1].plot(x, y2, '-',linewidth=1.0, color='yellow', label=fname)
        elif 'd4' in fname:
            ax[0].plot(x, y1, '-',linewidth=1.0, color='black', label=fname)
            ax[1].plot(x, y2, '-',linewidth=1.0, color='black', label=fname)
        elif 'd5' in fname:
            ax[0].plot(x, y1, '-',linewidth=1.0, color='purple', label=fname)
            ax[1].plot(x, y2, '-',linewidth=1.0, color='purple', label=fname)
        elif 'd6' in fname:
            ax[0].plot(x, y1, '-',linewidth=1.0, color='cyan', label=fname)
            ax[1].plot(x, y2, '-',linewidth=1.0, color='cyan', label=fname)

        ax[0].plot(x, df['100%'], '--',linewidth=1.0, color='red')
        ax[0].plot(x, df['75%'], '--',linewidth=1.0, color='red')
        ax[0].plot(x, df['50%'], '--',linewidth=1.0, color='red')
        ax[0].plot(x, df['25%'], '--',linewidth=1.0, color='red')
        ax[0].plot(x, df['5%'], '--',linewidth=1.0, color='red')

        ax[0].set_ylim([3500, 4500])
        ax[1].set_ylim([2500, 3900])

        ax[0].set_ylabel(y_label)
        ax[1].set_ylabel(y_label)
        # ax[0].legend(loc='upper right')
        
plt.xlabel(x_label)
plt.show()
