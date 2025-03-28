#!/usr/bin/env python3
from monitor import Monitor
import sys
import time

# Config File
import configparser
import threading
from copy import deepcopy

def read_file(file_name, max_bytes):
	f = open(file_name, "r")
	data = f.read()

	byte_data = data.encode("utf-8")  # Encode as UTF-8
	max_transfer = max_bytes - 35

	packets = []
	i = 1
	while True:
		packet_info = (str(i) + "||").encode("utf-8")
		transfer_room = max_transfer - len(packet_info)
		packets.append(packet_info + byte_data[:transfer_room])
		byte_data = byte_data[transfer_room:]

		if not byte_data: break
		i += 1

	return packets

class sender():
	def __init__(self, send_monitor, TRANS_DELAY, TIMEOUT, receiver_id, data_list, max_packet_size, window_size,
			  	target_ratio, kp, ki, kd):
		self.send_monitor_ = send_monitor
		self.send_monitor_.socketfd.settimeout(TIMEOUT)
		self.TRANS_DELAY_ = TRANS_DELAY
		self.TIMEOUT_ = TIMEOUT
		self.receiver_id_ = receiver_id
		self.data_list_ = data_list
		self.missing_packets_ = [*range(1, len(data_list) + 1)]
		self.max_packet_size_ = max_packet_size
		self.window_size_ = window_size
		self.new_missing_packets_ = deepcopy(self.missing_packets_)
		self.eow_flag = False

		# PID control
		self.target_ratio_ = target_ratio
		self.kp_ = kp
		self.ki_ = ki
		self.kd_ = kd
		self.integral_ = 0
		self.previous_error_ = 0
		self.max_window_size_ = len(self.missing_packets_)

	def send_packets(self):
		print(f'Sender: Sending Starts.')
		while self.missing_packets_:
			# send window size packet
			start_idx = 0
			end_idx = min(self.window_size_, len(self.missing_packets_) - 1)

			while end_idx < len(self.missing_packets_):
				end_idx = min(len(self.missing_packets_), start_idx + self.window_size_)
				for packet_idx in self.missing_packets_[start_idx : end_idx]:
					self.send_monitor_.send(self.receiver_id_, data_list[packet_idx-1])
					# print("send", packet_idx, end_idx, len(self.missing_packets_))
					time.sleep(self.TRANS_DELAY_)
				self.eow_flag = True
				start_idx = end_idx
			
			self.missing_packets_ = deepcopy(self.new_missing_packets_)
			self.max_window_size_ = len(self.missing_packets_)
			print("missing packet update", self.missing_packets_)

		print(f'Sender: Sending Done.')


	def window_ctr(self):
		num_recieved = 0
		while self.missing_packets_:
			try:
				addr, data = self.send_monitor_.recv(self.max_packet_size_)
				data = int(data.decode('utf-8'))

				if data in self.new_missing_packets_:
					self.new_missing_packets_.remove(data)
					num_recieved += 1

				# print(f'Sender: Got response for {data}/{len(self.data_list_)}. Window size: {self.window_size_} MAX: {self.max_window_size_}')
			except:
				a = 1
				# print(f'Sender: No response. Missing packets: {self.missing_packets_}')

			# A window sent
			if self.eow_flag:
				# PID contol window size
				current_ratio = num_recieved / self.window_size_
				error = self.target_ratio_ - current_ratio
				self.integral_ += error
				derivative = error - self.previous_error_
				adjustment = round(self.kp_ * error + self.ki_ * self.integral_ + self.kd_ * derivative)
				self.previous_error_ = error

				# update window size
				print(f"Window size: {self.window_size_} MAX: {self.max_window_size_} PID: {int(self.window_size_ - adjustment)} Ratio: {current_ratio} ADJ: {adjustment}")
				self.window_size_ = max(1, min(int(self.window_size_ - adjustment), self.max_window_size_))
				self.eow_flag = False
				num_recieved = 0

	
	def send_EOT(self):
		while True:
			self.send_monitor_.send(self.receiver_id_, b'EOT')
			try:
				addr, data = self.send_monitor_.recv(self.max_packet_size_)
				if data.decode('utf-8') == "Done":
					break
			except:
				continue
		
		self.send_monitor_.send_end(self.receiver_id_)


if __name__ == '__main__':
	config_path = sys.argv[1]

	# Initialize sender monitor
	send_monitor = Monitor(config_path, 'sender')
	
	# Parse config file
	cfg = configparser.RawConfigParser(allow_no_value=True)
	cfg.read(config_path)
	receiver_id = int(cfg.get('receiver', 'id'))
	file_to_send = cfg.get('nodes', 'file_to_send')
	max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
	data_list = read_file(file_to_send, max_packet_size)

	TRANS_DELAY = max_packet_size / int(cfg.get('network', 'LINK_BANDWIDTH'))
	TIMEOUT = 2 * float(cfg.get('network', 'PROP_DELAY')) + 2 * TRANS_DELAY + 1
	window_size = int(cfg.get('sender', 'window_size'))

	sd = sender(send_monitor, TRANS_DELAY, TIMEOUT, receiver_id, data_list, max_packet_size, window_size,
			  	target_ratio=0.70, kp=30.0, ki=0.5, kd=0.05)
			  	# target_ratio=0.90, kp=5.0, ki=0.1, kd=0.1)
			  	# target_ratio=0.90, kp=10.0, ki=0.2, kd=0.05)
		
	send_packets_thread = threading.Thread(target=sd.send_packets, daemon=True)
	window_ctr_thread = threading.Thread(target=sd.window_ctr, daemon=True)
	
	send_packets_thread.start()
	window_ctr_thread.start()
	send_packets_thread.join()
	window_ctr_thread.join()

	# send eot
	sd.send_EOT()