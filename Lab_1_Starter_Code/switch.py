#!/usr/bin/env python

"""This is the Switch Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
from datetime import date, datetime
import socket
import pdb

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
    def __init__(self, switch_id, server_ip, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_ip = server_ip
        self.port = port
        self.addr = (server_ip, port)
        self.switch_id = switch_id

        msg = self.switch_id.encode(encoding='UTF-8')
        self.client_socket.sendto(msg, self.addr)
        register_request_sent()
        self.get_server_info()
        register_response_received()
        self.get_routing_table()

    def get_server_info(self):
        (data, client_addr) = self.client_socket.recvfrom(self.port)

        data = data.decode('utf-8')[1:-1].split(')')[:-1]
        data = [i[i.find('(') + 1:].split(", ") for i in data]

        new_data = []
        for da in data:
            new_d = [int(da[0]), bool(da[1]), [da[2][2:-1], int(da[3][:-1])]]
            new_data.append(new_d)
        
        self.info = new_data
    
    def get_routing_table(self):
        (data, client_addr) = self.client_socket.recvfrom(self.port)
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

    
    def send_alive(self):
        msg = 'KEEP_ALIVE'.encode(encoding='UTF-8')
        self.client_socket.sendto(msg, self.addr)

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
    sw = switch(switch_id, server_ip, port)

    # while 

    # (data, client_addr) = client_socket.recvfrom(port)
    # register_response_received()
    # print(data)


if __name__ == "__main__":
    main()