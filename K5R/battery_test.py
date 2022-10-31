import os
from datetime import datetime as dt
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use("TkAgg")

LO_RES_TIME_FORMAT = '%04d%02d%02d'      # YYYYMMDD
HI_RES_TIME_FORMAT = '%04d%02d%02d-%02d%02d%02d'    #YYYYMMDD-HHMMSS

log_directory = '/Users/matt/Documents/Git/tools/K5R/logs_battery_k5r/User/'
PUFF_INDICATOR = 'puff stop'
COLOR_LIST = ['blue', 'blue', 'orange', 'magenta', 'black', 'green', 'cyan', 'purple', 'skyblue', 'chartreuse']

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
device_name = log_directory.split('/')[-3].split('_')[-1]
power_setting = log_directory.split('/')[-2]
print("Device: %s" % device_name)
print("Power Level: %s" % power_setting)

def run_df_calcs():
    t_start  = df['dut_ts'][0]
    df['timestamp'] = (df['dut_ts'] - t_start) * 1e-3
    df['100%'] = 4350
    df['75%'] = 4191
    df['50%'] = 4032
    df['25%'] = 3873
    df['5%'] = 3715

    sum_power = 0
    sum_count = 0
    for i in range(len(df['p_live'])):
        if df['p_live'][i] > 0:
            sum_power += df['p_live'][i]
            sum_count += 1
    df['average_power'] = sum_power / sum_count

fig, ax = plt.subplots(2, sharex=True)
if device_name == 'k5r':
    fig.suptitle('K5R - Max Power Setpoint: %s' % power_setting)
else:
    fig.suptitle('K5 - Max Power Setpoint: %s' % power_setting)
ax[0].title.set_text('Unloaded Battery Voltage')
ax[1].title.set_text('Power')

count = 0
fire_count = 0
current_dut = 1
previous_dut = 1
color_idx = 0

for file in file_list:
    if file.endswith('.log'):
        df = pd.DataFrame()
        df_data_lines = []
        file_path = log_directory + file
        f = open(file_path, 'r')
        r_lines = f.readlines()[4:]
        fire_count = 0

        for i in range(len(r_lines)):
            temp_line = r_lines[i].split(',')

            if PUFF_INDICATOR in r_lines[i]:
                fire_count += 1

            if (temp_line[0] == '$') and (len(temp_line) == (len(column_names) + 1)):
                try:
                    temp_line.pop(0)    # Remove '$'
                    temp_list = [float(j) for j in temp_line]
                    df_data_lines.append(temp_list)
                except:
                    pass

        count += 1
        print("%d: %s -> %d puffs" % (count, file, fire_count))
        f.close()
        df = pd.DataFrame(df_data_lines, columns=column_names)
        df = df.dropna()
        run_df_calcs()

        x = df['timestamp']
        x_label = 'Time (sec)'
        y1 = df['vbat_unloaded']
        y2 = df['p_live']
        y1_label = 'Voltage (mV)'
        y2_label = 'Power (mW)'

        fname = file.strip('.log')
        current_dut = fname.split('_')[1]

        if current_dut == previous_dut:
            ax[0].plot(x, y1, '-',linewidth=1.0, color=COLOR_LIST[color_idx])
            ax[1].plot(x, y2, '-',linewidth=1.0, color=COLOR_LIST[color_idx])
        else:
            color_idx += 1
            ax[0].plot(x, y1, '-',linewidth=1.0, color=COLOR_LIST[color_idx], label='dut%s' % (current_dut))
            ax[1].plot(x, y2, '-',linewidth=1.0, color=COLOR_LIST[color_idx], label='dut%s' % (current_dut))


        # ax[0].plot(x, df['100%'], '--',linewidth=1.0, color='red')
        # ax[0].plot(x, df['75%'], '--',linewidth=1.0, color='red')
        # ax[0].plot(x, df['50%'], '--',linewidth=1.0, color='red')
        # ax[0].plot(x, df['25%'], '--',linewidth=1.0, color='red')
        # ax[0].plot(x, df['5%'], '--',linewidth=1.0, color='red')

        ax[1].plot(x, df['average_power'], '--',linewidth=1.0, color='red')

        # ax[0].set_ylim([3500, 4500])
        # ax[1].set_ylim([2500, 3900])

        ax[0].set_ylabel(y1_label)
        ax[1].set_ylabel(y2_label)
        # ax.legend(loc='upper right')

        previous_dut = current_dut
        
plt.xlabel(x_label)
plt.show()
