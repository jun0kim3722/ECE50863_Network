#!/usr/bin/env python3
from monitor import Monitor
import sys
import time

# Config File
import configparser
from collections import deque

ENCRYPTION_KEY = b"RIC"
def xor_encrypt(data, key):
    return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

def read_file(file_name, max_bytes):
    f = open(file_name, "r")
    data = f.read()

    byte_data = data.encode("utf-8")  # Encode as UTF-8
    max_transfer = max_bytes - 35

    packets = []
    i = 0
    while True:
        packet_info = (str(i) + "|").encode("utf-8")
        transfer_room = max_transfer - len(packet_info)
        encrypted_payload = xor_encrypt(byte_data[:transfer_room], ENCRYPTION_KEY)
        packets.append(packet_info + encrypted_payload)
        byte_data = byte_data[transfer_room:]

        if not byte_data:
            break
        i += 1

    return packets


# def read_file(file_name, max_bytes):
# 	f = open(file_name, "r")
# 	data = f.read()

# 	byte_data = data.encode("utf-8")  # Encode as UTF-8
# 	max_transfer = max_bytes - 35

# 	packets = []
# 	i = 0
# 	while True:
# 		packet_info = (str(i) + "||").encode("utf-8")
# 		transfer_room = max_transfer - len(packet_info)
# 		packets.append(packet_info + byte_data[:transfer_room])
# 		byte_data = byte_data[transfer_room:]

# 		if not byte_data: break
# 		i += 1

# 	return packets

class sender():
	def __init__(self, send_monitor, TRANS_DELAY, TIMEOUT, receiver_id, data_list, max_packet_size, window_size,
			  	target_ratio, kp, ki, kd):
		self.send_monitor_ = send_monitor
		self.send_monitor_.socketfd.settimeout(TIMEOUT)
		self.TRANS_DELAY_ = TRANS_DELAY
		self.TIMEOUT_ = TIMEOUT
		self.receiver_id_ = receiver_id
		self.data_list_ = data_list
		self.missing_packets_ = deque([*range(len(data_list))])
		self.max_packet_size_ = max_packet_size
		self.window_size_ = window_size
		# self.new_missing_packets_ = set()
		self.eow_flag = False

		# PID control
		self.target_ratio_ = target_ratio
		self.kp_ = kp
		self.ki_ = ki
		self.kd_ = kd
		self.integral_ = 0
		self.previous_error_ = 0
		self.max_window_size_ = len(self.missing_packets_)
		self.first_run = True

	def send_packets(self):
		print(f'Sender: Sending Starts.')
		while self.missing_packets_:
			# send window size packet
			start_idx = 0
			end_idx = 0
			while self.missing_packets_:
				window_size = min(len(self.missing_packets_), self.window_size_)

				for _ in range(window_size):
					packet_idx = self.missing_packets_.popleft()
					self.send_monitor_.send(self.receiver_id_, data_list[packet_idx])
					time.sleep(self.TRANS_DELAY_)
				
				# update missing_packets_ and window_size_
				self.window_ctr(packet_idx)

		self.send_EOT()


	def window_ctr(self, end_id):
		num_recieved = 0
		while True:
			# send EOW & get missing packets
			self.send_monitor_.send(self.receiver_id_, b'EOW')

			try:
				addr, data = self.send_monitor_.recv(self.max_packet_size_)
				data = data.decode('utf-8')

				split_idx = data.find("|")
				max_id = int(data[split_idx+1:])
				missing_packets = {*range(max_id+1, end_id)}

				if data[1:split_idx-1]:
					missing_packets |= {int(i) for i in data[1:split_idx-1].split(',')}
				
				num_recieved = self.window_size_ - len(missing_packets)
				missing_packets.difference_update(set(self.missing_packets_))
				self.missing_packets_.extendleft(missing_packets) # priorities missing packets
				
				# print(f'Sender: Got response for {num_recieved}/{self.window_size_} {missing_packets}')

				# PID contol window size
				current_ratio = num_recieved / self.window_size_
				error = self.target_ratio_ - current_ratio
				self.integral_ += error
				derivative = error - self.previous_error_
				adjustment = round(self.kp_ * error + self.ki_ * self.integral_ + self.kd_ * derivative)
				self.previous_error_ = error

				# update window size
				print(f"New window size: {self.window_size_} PID: {int(self.window_size_ - adjustment)} Ratio: {current_ratio} ADJ: {-adjustment}")
				# self.window_size_ = max(1, min(int(self.window_size_ - adjustment), self.max_window_size_))
				break

			except:
				continue
	
	def send_init(self):
		while True:
			send_monitor.send(self.receiver_id_, str(len(data_list)).encode('utf-8'))

			try:
				addr, data = send_monitor.recv(self.max_packet_size_)
				break
			except:
				print("Init FAILED!!!")

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
		print(f'Sender: Sending Done.')


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
			  	target_ratio=0.90, kp=10.0, ki=0.2, kd=0.05)
			  	# target_ratio=0.50, kp=30.0, ki=0.5, kd=0.05)
			  	# target_ratio=0.70, kp=5.0, ki=0.1, kd=0.1)
	sd.send_packets()