#!/usr/bin/env python3
from monitor import Monitor
import sys
from copy import deepcopy

# Config File
import configparser

ENCRYPTION_KEY = b"RIC"
def xor_decrypt(data, key):
	return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])


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
	saperator = '|'.encode()

	# Exchange messages!
	data_list = {}
	recv = []
	prev_recv = []
	while True:
		addr, data = recv_monitor.recv(max_packet_size)

		if data == b"EOT":
			recv_monitor.send(sender_id, b"Done")
			break

		if data == b"EOW":
			# send NACK
			max_id = max(data_list.keys())
			missing_packets = list(set(range(max_id)).difference(set(data_list.keys())))
			msg = str(missing_packets) + "|" + str(max_id)
			recv_monitor.send(sender_id, msg.encode('utf-8'))
			continue

		# get nums
		cut = data.find(saperator)
		if cut == -1:
			print(f"Error processing packet")
			continue

		
		packet_idx = data[:cut]
		packet_id = int(packet_idx.decode('utf-8'))
		encrypted_msg = data[cut+1:]
		msg = xor_decrypt(encrypted_msg, ENCRYPTION_KEY)  # Decrypt payload

		data_list[packet_id] = msg
		print("Recieved: ", packet_id)

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