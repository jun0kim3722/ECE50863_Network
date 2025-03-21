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
	missing_packets = [1]
	data_list = {}
	while True:
		addr, data = recv_monitor.recv(max_packet_size)

		if data == b'EOT':
			if not missing_packets:
				recv_monitor.send(sender_id, "Done".encode('utf-8'))
				break
			else:
				recv_monitor.send(sender_id, str(missing_packets).encode('utf-8'))
				print('Sent :', missing_packets)
				continue

		# get nums
		cut = data.find(saperator)

		if cut == -1:
			# get init info
			recv_monitor.send(sender_id, b"ACK")
			total_packet_size = int(data.decode('utf-8'))
			missing_packets = [*range(1, total_packet_size + 1)]
			continue
		
		packet_idx = data[:cut]
		missing_packets.remove(int(packet_idx.decode('utf-8')))
		print(missing_packets)

		msg = data[cut+2:]
		data_list[packet_idx] = msg


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