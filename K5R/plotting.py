import json
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use("TkAgg")

# DVC_CONFIG = "K3"
DVC_CONFIG = "K5R"

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
					if DVC_CONFIG == "K3":
						temp_line = r_lines[i].split(";")
						if (len(temp_line) == len(self.config["DATA_HEADERS"].keys()) + 1):
							temp_line.pop(len(self.config["DATA_HEADERS"].keys())) 	# Remove ''
							temp_list = [float(j) for j in temp_line]
							df_data_lines.append(temp_list)
					else:
						temp_line = r_lines[i].split(",")
						if temp_line[0] == '$' and (len(temp_line) == len(self.config["DATA_HEADERS"].keys()) + 1):
							try:
								temp_line.pop(0) 	# Remove '$'
								temp_list = [float(j) for j in temp_line]
								df_data_lines.append(temp_list)
							except:
								pass

			else:
				print('Data file is empty!')
				rtn_val = False
			f.close()
			if rtn_val:
				# try:
				self.df = pd.DataFrame(df_data_lines, columns=self.headers[:len(self.config["DATA_HEADERS"].keys())])
				self.df = self.df.dropna()
				self.run_df_calcs()
				print(self.df)
				# except:
					# print('Bad pandas import of file!')
					# rtn_val = False
		else:
			print('Data file must be a LOG file!')
			rtn_val = False
		return rtn_val

	def run_df_calcs(self):
		if DVC_CONFIG == "K3":
			pass
		else:
			t_start  = self.df['time_stamp'][0]
			self.df['time_stamp'] = (self.df['time_stamp'] - t_start) * 1e-3

			# self.df['tcr_temp'] = (((self.df['r_targ'] - self.df['r_base'])/self.df['r_base']) / 0.000415) + 29
			# self.df['tcr_live'] = (((self.df['r_live'] - self.df['r_base'])/self.df['r_base']) / 0.000415) + 29
			# self.df['r_targ_plus'] = self.df['r_targ'] + 50
			# self.df['r_targ_minus'] = self.df['r_targ'] - 50
			# overshoot = self.df['r_live'].max() - self.df['r_targ'].iat[-1]
			# temp_overshoot = ((overshoot / self.df['r_base'].iat[-1]) / 0.000415)
			# print("Overshoot: %.2fmΩ\r\nTemp Overshoot: %.2f˚C" % (overshoot * 0.1, temp_overshoot))
			# self.df['r_base_plus'] = self.df['r_base'] + 100
			# self.df['r_diff_avg'] = self.df['r_diff_avg'] * 0.1
			# self.df['offset'] = -4
			# self.df['r_base_minus'] = self.df['r_base'] - 25
			# self.df['r_live_plus'] = self.df['r_live'] + 25
			# self.df['r_live_minus'] = self.df['r_live'] - 25
			# energy = self.df['p_live'] * self.df['time_stamp'].diff()
			# energy_total = energy.cumsum().max() * 1e-3
			# print('Energy = %.3fJ' % energy_total)
			# self.df['r_live'] *= 0.1
			# self.df['r_base'] *= 0.1
			# self.df['r_targ'] *= 0.1
			# self.df['p_desired'] *= 1e-3
			# self.df['p_actual'] *= 1e-3
			# self.df['duty'] = (self.df['duty'] / MAX_DUTY_TICKS) * 100
			# self.df['fixed_offset_plus'] = 300
			# self.df['fixed_offset_minus'] = -300
			# self.df['fixed_offset_plus1'] = 300
			# self.df['fixed_offset_minus1'] = -300

	def run(self):
		for k,v in self.config.items():
			if "PLOT_WINDOW" in k:
				num_sub_plots = len(v.keys()) - 2 		# Excludes 'title' and 'x_data' in plot window's dict
				fig, ax = plt.subplots(num_sub_plots, sharex=True)
				fig.suptitle(v['title'])
				for i in range(num_sub_plots):
					x = self.df[self.headers[v['x_data'][0] - 1]]
					x_label = self.hlabels[v['x_data'][0] - 1]
					num_traces = len(v['subplot%d' % (i+1)])
					for trace in v['subplot%d' % (i+1)]:
						y = self.df[self.headers[trace - 1]]
						if num_sub_plots > 1:
							if DVC_CONFIG == "K3":
								ax[i].plot(y, label=self.headers[trace - 1])
							else:
								ax[i].plot(x, y, label=self.headers[trace - 1])
							ax[i].set_ylabel(self.hlabels[trace - 1])
							ax[i].legend(loc='upper right')
						else:
							if DVC_CONFIG == "K3":
								ax.plot(y, label=self.headers[trace - 1])
							else:
								ax.plot(x, y, label=self.headers[trace - 1])
							ax.set_ylabel(self.hlabels[trace - 1])
							ax.legend(loc='upper right')
				# ax[2].plot(self.df['time_stamp'], self.df['tcr_temp'])
				# ax[2].plot(self.df['time_stamp'], self.df['tcr_live'])
				# ax[2].plot(self.df['time_stamp'], self.df['tcr_temp_plus'])
				# ax[2].plot(self.df['time_stamp'], self.df['tcr_temp_minus'])
				# ax[0].plot(self.df['time_stamp'], self.df['r_targ_plus'])
				# ax[0].plot(self.df['time_stamp'], self.df['r_targ_minus'])
				# ax[0].plot(self.df['time_stamp'], self.df['r_live_plus'])
				# ax[0].plot(self.df['time_stamp'], self.df['r_live_minus'])
				# ax[2].plot(self.df['time_stamp'],self.df['fixed_offset_plus'])
				# ax[2].plot(self.df['time_stamp'],self.df['fixed_offset_minus'])
				# ax[3].plot(self.df['time_stamp'],self.df['fixed_offset_plus1'])
				# ax[3].plot(self.df['time_stamp'],self.df['fixed_offset_minus1'])
				# ax[1].plot(self.df['time_stamp'],self.df['offset'])

				if DVC_CONFIG != "K3":
					plt.xlabel(x_label)
		plt.show()

plotter = PLOTTER()
# plotter.load_config_file('/Users/matt/Documents/Projects/DHD/GUI/configs/pax_fury_config.json')
# plotter.load_data_file('/Users/matt/Documents/Projects/DHD/GUI/logs/20220114-125551.log')
# plotter.run()

