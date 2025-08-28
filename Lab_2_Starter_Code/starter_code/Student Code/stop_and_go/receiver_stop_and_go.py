#!/usr/bin/env python3
from monitor import Monitor
import sys

# Config File
import configparser

if __name__ == '__main__':
	print("Receivier starting up!")
	config_path = sys.argv[1]

	# Initialize sender monitor
	recv_monitor = Monitor(config_path, 'receiver')
	
	# Parse config file
	cfg = configparser.RawConfigParser(allow_no_value=True)
	cfg.read(config_path)
	sender_id = int(cfg.get('sender', 'id'))
	file_to_send = cfg.get('nodes', 'file_to_send')
	max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
	saperator = '||'.encode()

	# Exchange messages!
	data_list = {}
	while True:
		addr, data = recv_monitor.recv(max_packet_size)
		recv_monitor.send(sender_id, b'ACK')

		if data == b'EOT':
			break

		# get nums
		cut = data.find(saperator)
		packet_idx = data[:cut]
		msg = data[cut+2:]
		data_list[packet_idx] = msg

		print(packet_idx)

	# write data
	f = open("received_file.txt", "w")
	try:
		joined = b"".join([data_list[key] for key in sorted(data_list, key=lambda k: int(k))])
		full_data = joined.decode("utf-8")
	except:
		breakpoint()

	f.write(full_data)

	# Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
	recv_monitor.recv_end('received_file.txt', sender_id)
