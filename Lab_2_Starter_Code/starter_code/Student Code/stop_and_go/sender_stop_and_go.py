#!/usr/bin/env python3
from monitor import Monitor
import sys

# Config File
import configparser

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
	data_list.append(b'EOT')

	# Exchange messages!
	print(f'Sender: Sending Starts.')

	TRANS_DELAY = max_packet_size / int(cfg.get('network', 'LINK_BANDWIDTH'))
	TIMEOUT = 2 * float(cfg.get('network', 'PROP_DELAY')) + 2 * TRANS_DELAY + 1
	send_monitor.socketfd.settimeout(TIMEOUT)

	for i in range(len(data_list)):
		while True:
			send_monitor.send(receiver_id, data_list[i])

			try:
				addr, data = send_monitor.recv(max_packet_size)
				break
			except:
				print("FAILED!!!")

		print(f'Sender: Got response from id {addr}: {data} for idx {i+1}/{len(data_list)}')
	
	# Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
	send_monitor.send_end(receiver_id)
