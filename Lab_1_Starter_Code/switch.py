#!/usr/bin/env python

"""This is the Switch Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
from datetime import date, datetime
import socket
import threading
import time

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "switch#.log" # The log file for switches are switch#.log, where # is the id of that switch (i.e. switch0.log, switch1.log). The code for replacing # with a real number has been given to you in the main function.

# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request Sent

def register_request_sent():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request Sent\n")
    write_to_log(log)

# "Register Response" Format is below:
#
# Timestamp
# Register Response Received

def register_response_received():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response received\n")
    write_to_log(log) 

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>.
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>
# ...
# ...
# Routing Complete
# 
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Unresponsive/Dead Neighbor Detected" Format is below:
#
# Timestamp
# Neighbor Dead <Neighbor ID>

def neighbor_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Dead {switch_id}\n")
    write_to_log(log)

# "Unresponsive/Dead Neighbor comes back online" Format is below:
#
# Timestamp
# Neighbor Alive <Neighbor ID>

def neighbor_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Alive {switch_id}\n")
    write_to_log(log)

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

class switch:
    def __init__(self, switch_id, server_ip, port, fail_link):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_ip = server_ip
        self.port = port
        self.server_addr = (server_ip, port)
        self.switch_id = switch_id
        self.update_flag = False
        self.fail_link = fail_link

        msg = self.switch_id.encode(encoding='UTF-8')
        self.client_socket.sendto(msg, self.server_addr)
        register_request_sent()
        self.get_server_info()
        register_response_received()

        (data, client_addr) = self.client_socket.recvfrom(self.port)
        while client_addr != self.server_addr:
            (data, client_addr) = self.client_socket.recvfrom(self.port)
        self.get_routing_table(data)
        print('INIT setup done')

    def get_server_info(self):
        (data, client_addr) = self.client_socket.recvfrom(self.port)
        data = data[4:]
        data = data.decode('utf-8')[1:-1].split(')')[:-1]
        data = [i[i.find('(') + 1:].split(", ") for i in data]

        new_data = []
        for da in data:
            new_d = [int(da[0]), bool(da[1]), [da[2][2:-1], int(da[3][:-1])]]
            new_data.append(new_d)
        
        self.info = new_data
        print(self.info)

    def update_server_info(self, data):
        data = data.decode('utf-8')[1:-1].split(')')[:-1]
        data = [i[i.find('(') + 1:].split(", ") for i in data]

        new_data = []
        for i, da in enumerate(data):
            if not self.info[i][1] and da[1]:
                print(self.info[i][1], da[1])
                neighbor_alive(self.info[i][0])

            new_d = [int(da[0]), bool(da[1]), [da[2][2:-1], int(da[3][:-1])]]
            new_data.append(new_d)
        
        self.info = new_data
        print(self.info)



    def get_routing_table(self, data):
        data = data.decode('utf-8').split("\n")[:-1]

        self.routing_table = []
        for line in data:
            new_line = []
            string = line.split(':')
            for i in string:
                nums = i.split(',')
                new_line += [int(num) for num in nums]
            self.routing_table.append(new_line)

        routing_table_update(self.routing_table)
    
    def sender(self):
        alive_msg = (str(self.switch_id) + 'KEEP_ALIVE').encode(encoding='UTF-8')

        while True:
            time.sleep(2.0)

            msg = str(self.switch_id) + ':' + ",".join([str(nhb[0]) for nhb in self.info if nhb[1]])
            self.client_socket.sendto(msg.encode('UTF-8'), self.server_addr)
            
            for nhb in self.info:
                if nhb[0] == self.fail_link:
                    continue

                self.client_socket.sendto(alive_msg, tuple(nhb[2]))

    def receiver(self):
        while True:
            for nhb in self.info:
                is_received = False
                is_info_updated = False
                st = time.time()
                while time.time() - st < 6:
                    port = nhb[2][1]
                    data, sender_addr = self.client_socket.recvfrom(port)

                    if sender_addr[1] == port:
                        is_received = True
                        print('recive from', nhb[0])
                        break
                
                    elif sender_addr == self.server_addr:
                        print(data)
                        if data[:5] == 'info:'.encode('UTF-8'):
                            self.update_server_info(data)
                            is_info_updated = True
                            # time.sleep(2)
                            break

                        self.get_routing_table(data)
    
                if is_info_updated:
                    break

                elif not is_received and nhb[1]:
                    neighbor_dead(nhb[0])
                    nhb[1] = is_received
                

def main():
    global LOG_FILE

    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 4:
        print ("switch.py <Id_self> <Controller hostname> <Controller Port>\n")
        sys.exit(1)

    my_id = int(sys.argv[1])
    LOG_FILE = 'switch' + str(my_id) + ".log"

    # Write your code below or elsewhere in this file
    port = int(sys.argv[3])
    server_ip = sys.argv[2]
    switch_id = sys.argv[1]

    fail_link = -1
    if len(sys.argv) > 5:
        fail_link = int(sys.argv[5])


    sw = switch(switch_id, server_ip, port, fail_link)

    # periodic operation
    receiver_thread = threading.Thread(target=sw.receiver, daemon=True)
    sender_thread = threading.Thread(target=sw.sender, daemon=True)
    receiver_thread.start()
    sender_thread.start()

    receiver_thread.join()
    sender_thread.join()

    while True:
        print("")



if __name__ == "__main__":
    main()