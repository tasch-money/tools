import json
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use("TkAgg")

LOGFILE_HEADER_SKIP = 4
MAX_DUTY_TICKS = 656

PWM_HEATING_DUTY_CYCLE = 0.875
PWM_VBAT_LOADED_DUTY_CYCLE = 0.006

class PLOTTER:
	def __init__(self):
		self.config = {}
		self.df = pd.DataFrame()
		self.headers = []
		self.num_data_headers = 0
		self.extra_calcs_flag = False

		self.r_targ = 0
		self.r_base = 0
		self.t_targ = 0
		self.tcr = 0
		self.puff_start_time = 0
		self.puff_counter = 0
		self.puff_start_flag = False
		self.puff_duration = []

	def load_config_file(self, file):
		if file.endswith('.json'):
			try:
				f = open(file)
				self.config = json.load(f)
				f.close()

				try:
					self.headers = [None] * (len(self.config["DATA_HEADERS"].keys()) + len(self.config["CALCULATIONS"].keys()))
					self.extra_calcs_flag = True
				except:
					self.headers = [None] * len(self.config["DATA_HEADERS"].keys())
					self.extra_calcs_flag = False
				self.num_data_headers = len(self.config["DATA_HEADERS"].keys())
				self.hlabels = [None] * len(self.config["HEADERS_LABELS"].keys())

				# Organize list of data headers and labels (used for data frame labeling and plot axis labeling)
				for k,v in self.config["DATA_HEADERS"].items():
					loc = int(k) - 1
					self.headers[loc] = v
					self.hlabels[loc] = self.config["HEADERS_LABELS"][k]
				if self.extra_calcs_flag:
					for k,v in self.config["CALCULATIONS"].items():
						loc = int(k) - 1
						self.headers[loc] = v
						self.hlabels[loc] = self.config["HEADERS_LABELS"][k]

			except:
				print('Configuration file selected is not properly formated for JSON!')
		else:
			print('Configuration file must be JSON!')

	def load_data_file(self, file):
		rtn_val = True
		if file.endswith('.log'):
			f = open(file, 'r')
			r_lines = f.readlines()
			if len(r_lines) > 10:
				df_data_lines = []
				self.r_targ = 0
				self.r_base = 0
				self.t_targ = 0
				self.tcr = 0
				self.puff_start_time = 0
				self.puff_counter = 0
				self.puff_start_flag = False
				self.puff_duration = []
				for i in range(len(r_lines)):
					temp_line = r_lines[i].split(',')
					if 'setpt' in temp_line[0]:
						temp_line = r_lines[i].split(' ')
						self.puff_counter += 1
						self.puff_start_flag = True
						prev_line = r_lines[i - 1].split(',')
						if '$' in prev_line[0]:
							self.puff_duration.append(float(prev_line[1]) - self.puff_start_time)
						if self.puff_counter >= 2:
							new_zero_line = df_data_lines[-1]
							new_zero_line[0] = float(new_zero_line[0]) + 8
							new_zero_line[1] = self.r_base
							new_zero_line[2] = 0
							new_zero_line[3] = 0
							df_data_lines.append(new_zero_line)

						self.r_targ = float(temp_line[1])
						if 'basel' in temp_line[2]:
							self.r_base = float(temp_line[3])
						if 'trgt' in temp_line[13]:
							self.t_targ = float(temp_line[14])
						if 'tcr' in temp_line[15]:
							self.tcr = float(temp_line[16].strip())

					if temp_line[0] == '$' and temp_line[1] != 'time':
						try:
							temp_line.pop(0) 	# Remove '$'
							temp_list = [float(j) for j in temp_line]
							temp_list.append(self.r_targ)
							temp_list.append(self.r_base)
							temp_list.append(self.t_targ)
							temp_list.append(self.tcr)
							if self.puff_start_flag:
								self.puff_start_flag = False
								self.puff_start_time = float(temp_line[1])
								
								if self.puff_counter >= 2:
									new_zero_line = temp_list
									new_zero_line[0] = float(temp_list[0]) - 8
									new_zero_line[1] = self.r_base
									new_zero_line[2] = 0
									new_zero_line[3] = 0
									df_data_lines.append(new_zero_line)

								df_data_lines.append(temp_list)
							else:
								df_data_lines.append(temp_list)
						except:
							pass
			else:
				print('Data file is empty!')
				rtn_val = False
			f.close()
			if rtn_val:
				try:
					self.df = pd.DataFrame(df_data_lines, columns=self.headers[:len(self.config["DATA_HEADERS"].keys())])
					self.df = self.df.dropna()
					self.run_df_calcs()
					# print(self.df)
				except:
					print('Bad pandas import of file!')
					rtn_val = False
		else:
			print('Data file must be a LOG file!')
			rtn_val = False
		return rtn_val

	def run_df_calcs(self):
		t_start  = self.df['time_stamp'][0]
		self.df['time_stamp'] = (self.df['time_stamp'] - t_start) * 1e-3
		self.df['duty_cycle'] = 100 * (self.df['duty_cycle'] / MAX_DUTY_TICKS)
		if self.extra_calcs_flag:
			for k,v in self.config["CALCULATIONS"].items():
				if v == 'power':
					R = self.df['r_coil_live'] * 0.001
					duty = self.df['duty_cycle'] * 0.01
					vbat = self.df['vbat'] * 0.001
					self.df[v] = ((vbat * vbat) / R) * (duty * PWM_HEATING_DUTY_CYCLE + PWM_VBAT_LOADED_DUTY_CYCLE)
		self.df.loc[~np.isfinite(self.df['power']), 'power'] = 0

	def run(self):
		for k,v in self.config.items():
			if "PLOT_WINDOW" in k:
				num_sub_plots = len(v.keys()) - 2 		# Excludes 'title' and 'x_data' in plot window's dict
				fig, ax = plt.subplots(num_sub_plots, sharex=True)
				fig.suptitle(v['title'] + " - TCR = %dppm/˚C" % self.tcr)
				for i in range(num_sub_plots):
					x = self.df[self.headers[v['x_data'][0] - 1]]
					x_label = self.hlabels[v['x_data'][0] - 1]
					num_traces = len(v['subplot%d' % (i+1)])
					for trace in v['subplot%d' % (i+1)]:
						y = self.df[self.headers[trace - 1]]
						if num_sub_plots > 1:
							ax[i].plot(x, y, label=self.headers[trace - 1])
							ax[i].set_ylabel(self.hlabels[trace - 1])
							ax[i].legend(loc='upper right')
						else:
							ax.plot(x, y, label=self.headers[trace - 1])
							ax.set_ylabel(self.hlabels[trace - 1])
							ax.legend(loc='upper right')
				plt.xlabel(x_label)
		plt.show()

plotter = PLOTTER()
# plotter.load_config_file('/Users/matt/Documents/Projects/DHD/GUI/configs/pax_fury_config.json')
# plotter.load_data_file('/Users/matt/Documents/Projects/DHD/GUI/logs/20220114-125551.log')
# plotter.run()

