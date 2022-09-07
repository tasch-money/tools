import os
from datetime import datetime as dt
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use("TkAgg")

LO_RES_TIME_FORMAT = '%04d%02d%02d'      # YYYYMMDD
HI_RES_TIME_FORMAT = '%04d%02d%02d-%02d%02d%02d'    #YYYYMMDD-HHMMSS

log_directory = '/Users/matt/Documents/Git/tools/K5/Data Logger/logs/'

column_names = [
    'timestamp',
    'r_live',
    'r_base',
    'r_targ',
    'r_live_avg',
    'r_end_heating',
    'r_ratio',
    'r_ratio_live',
    'hot_count',
    'cool_count'
]

file_list = os.listdir(log_directory)
file_list.sort()

def run_df_calcs():
    t_start  = df['timestamp'][0]
    df['timestamp'] = (df['timestamp'] - t_start) * 1e-3
    df['r_base_plus'] = df['r_base'] + 25
    df['r_base_minus'] = df['r_base'] - 25
    # df['r_ratio_plus'] = 500
    # df['r_ratio_minus'] = -500


fig, ax = plt.subplots(1, sharex=True)
fig.suptitle('Model Raw Data')

count = 0
for file in file_list:
    if file.endswith('.csv'):
        count += 1
        print("%d: %s" % (count, file))
        df = pd.DataFrame()
        df_data_lines = []
        file_path = log_directory + file
        f = open(file_path, 'r')
        r_lines = f.readlines()[4:]

        for i in range(len(r_lines)):
            temp_line = r_lines[i].split(',')

            if temp_line[0] == '$':
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
        y1 = df['r_ratio']
        y2 = df['r_ratio_live']
        y1_label = 'Ratio'
        # if file == '20220720-134925.csv':
        #     ax.plot(x, y1, '-',linewidth=3.0, color='black', label='puff %d' % count)
        # else:
        heating_time = df['hot_count'].max() * 0.008

        if heating_time <= 2:
            ax.plot(x, y2, '-',linewidth=1.0, color='blue', label='%.3f sec' % heating_time)
        elif heating_time <= 3.3:
            ax.plot(x, y2, '-',linewidth=1.0, color='green', label='%.3f sec' % heating_time)
        elif heating_time <= 5.5:
            ax.plot(x, y2, '-',linewidth=1.0, color='red', label='%.3f sec' % heating_time)
        elif heating_time <= 7:
            ax.plot(x, y2, '-',linewidth=1.0, color='yellow', label='%.3f sec' % heating_time)
        else:
            ax.plot(x, y2, '-',linewidth=1.0, color='black', label='%.3f sec' % heating_time)

        # ax.plot(x, y2, '-',linewidth=1.0, label='puff %d' % count)
        # if 5 < count <= 25:
        #     if count == 22:
        #         ax.plot(x, y1, '-',linewidth=3.0, color='black', label='puff %d' % count)
        #         print(file)
        #     else:
        #         ax.plot(x, y1, 'x',linewidth=1.0, label='puff %d' % count)
        # elif count <= 35:
        #     ax.plot(x, y1, '+',linewidth=1.0, label='puff %d' % count)
        # elif count <= 45:
        #     ax.plot(x, y1, '-',linewidth=1.0, label='puff %d' % count)
        ax.set_ylabel(y1_label)
        ax.legend(loc='upper right')
        # ax.plot(df['timestamp'],df['fixed_offset_plus'])
        # ax.plot(df['timestamp'],df['fixed_offset_minus'])
plt.xlabel(x_label)
plt.show()
