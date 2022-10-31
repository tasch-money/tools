import os
from datetime import datetime as dt
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use("TkAgg")

TCR_NEW = 445
TCR_POR = 415

log_directory = '/Users/matt/Documents/Git/tools/K5R/logs_tcr/'

column_names = [
    'channel_1',
    'channel_2',
    'channel_3',
    'channel_4',
    'channel_5',
    'channel_6',
    'channel_7',
    'channel_8',
    'oven_temp'
]

file_list = os.listdir(log_directory)
file_list.sort()

def run_df_calcs():
    r1_base = df['channel_1'][0]
    r2_base = df['channel_2'][0]
    r3_base = df['channel_3'][0]
    r4_base = df['channel_4'][0]
    r5_base = df['channel_5'][0]
    r6_base = df['channel_6'][0]
    r7_base = df['channel_7'][0]
    r8_base = df['channel_8'][0]
    df['dR1'] = df['channel_1'] / r1_base - 1
    df['dR2'] = df['channel_2'] / r2_base - 1
    df['dR3'] = df['channel_3'] / r3_base - 1
    df['dR4'] = df['channel_4'] / r4_base - 1
    df['dR5'] = df['channel_5'] / r5_base - 1
    df['dR6'] = df['channel_6'] / r6_base - 1
    df['dR7'] = df['channel_7'] / r7_base - 1
    df['dR8'] = df['channel_8'] / r8_base - 1

    # df['tcr_model'] = 0.000545 * df['oven_temp'] + 1.212
    df['tcr_new'] = TCR_NEW * 1e-6 * df['oven_temp'] - 0.03
    df['tcr_por'] = TCR_POR * 1e-6 * df['oven_temp'] - 0.03


# fig1, ax1 = plt.subplots(2, sharex=True)
# fig1.suptitle('TCR = %s' % TCR)

fig2, ax2 = plt.subplots(1, sharex=True)
fig2.suptitle('TCR NEW = %s\nTCR POR = %s' % (TCR_NEW, TCR_POR))

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

            if (len(temp_line) == len(column_names)):
                temp_list = [float(j) for j in temp_line]
                for k in range(len(temp_list)):
                    if (k < (len(temp_list) - 1)) and (temp_list[k] > 5):
                        temp_list[k] = 0
                df_data_lines.append(temp_list)
        f.close()
        df = pd.DataFrame(df_data_lines, columns=column_names)
        df = df.dropna()
        run_df_calcs()

        # ax1[0].plot(df['channel_1'])
        # ax1[0].plot(df['channel_2'])
        # ax1[0].plot(df['channel_3'])
        # ax1[0].plot(df['channel_4'])
        # ax1[1].plot(df['oven_temp'])
        # ax1[0].set_ylabel('Resistance (Ω)')
        # ax1[1].set_ylabel('Temperature (˚C)')
        # ax1[1].set_xlabel('Sample')

        ax2.plot(df['oven_temp'], df['dR1'], '-', linewidth=1.0, color='blue', label='coil_1')
        ax2.plot(df['oven_temp'], df['dR2'], '-', linewidth=1.0, color='green', label='coil_2')
        ax2.plot(df['oven_temp'], df['dR3'], '-', linewidth=1.0, color='orange', label='coil_3')
        ax2.plot(df['oven_temp'], df['dR4'], '-', linewidth=1.0, color='red', label='coil_4')
        ax2.plot(df['oven_temp'], df['dR5'], '-', linewidth=1.0, color='magenta', label='coil_5')
        ax2.plot(df['oven_temp'], df['dR6'], '-', linewidth=1.0, color='black', label='coil_6')
        ax2.plot(df['oven_temp'], df['dR7'], '-', linewidth=1.0, color='cyan', label='coil_7')
        ax2.plot(df['oven_temp'], df['dR8'], '-', linewidth=1.0, color='yellow', label='coil_8')
        # ax2.plot(df['oven_temp'], df['tcr_new'], '--', linewidth=2.0, color='red', label='NEW')
        # ax2.plot(df['oven_temp'], df['tcr_por'], '--', linewidth=2.0, color='green', label='POR')
        ax2.set_ylabel('%∆R')
        ax2.set_xlabel('Temperature (˚C)')

        ax2.legend(loc='upper right')
        
plt.show()
