#!/usr/bin/env python

"""This is the Controller Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
from datetime import date, datetime
import socket
import heapq
from copy import deepcopy

import pdb

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "Controller.log"

# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request <Switch-ID>

def register_request_received(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request {switch_id}\n")
    write_to_log(log)

# "Register Responses" Format is below (for every switch):
#
# Timestamp
# Register Response <Switch-ID>

def register_response_sent(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response {switch_id}\n")
    write_to_log(log) 

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>, and the fourth is <Shortest distance>
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>,<Shortest distance>
# ...
# ...
# Routing Complete
#
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4,0
# 0 indicates ‘zero‘ distance
#
# For switches that can’t be reached, the next hop and shortest distance should be ‘-1’ and ‘9999’ respectively. (9999 means infinite distance so that that switch can’t be reached)
#  E.g, If switch=4 cannot reach switch=5, the following should be printed
#  4,5:-1,9999
#
# For any switch that has been killed, do not include the routes that are going out from that switch. 
# One example can be found in the sample log in starter code. 
# After switch 1 is killed, the routing update from the controller does not have routes from switch 1 to other switches.

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    # for row in routing_table:
    for main_key in routing_table.keys():
        for dist_key in routing_table[main_key][0].keys():
            if main_key != dist_key:
                log.append(f"{main_key},{dist_key}:{routing_table[main_key][1][dist_key][0]},{routing_table[main_key][0][dist_key]}\n")
            else:
                log.append(f"{main_key},{dist_key}:{main_key},{routing_table[main_key][0][dist_key]}\n")

    log.append("Routing Complete\n")
    write_to_log(log)

# "Topology Update: Link Dead" Format is below: (Note: We do not require you to print out Link Alive log in this project)
#
#  Timestamp
#  Link Dead <Switch ID 1>,<Switch ID 2>

def topology_update_link_dead(switch_id_1, switch_id_2):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Link Dead {switch_id_1},{switch_id_2}\n")
    write_to_log(log) 

# "Topology Update: Switch Dead" Format is below:
#
#  Timestamp
#  Switch Dead <Switch ID>

def topology_update_switch_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Dead {switch_id}\n")
    write_to_log(log) 

# "Topology Update: Switch Alive" Format is below:
#
#  Timestamp
#  Switch Alive <Switch ID>

def topology_update_switch_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

class server:
    def __init__(self, port, filename):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(("127.0.0.1", port))
        self.read_graph(filename)

    def read_graph(self, filename):
        with open(filename, "r") as f:
            lines = f.readlines()
        
        info = []
        num_switch = int(lines[0][:-1])
        for i in range(1, len(lines)):
            info.append([int(j) for j in lines[i][:-1].split(' ')])
        
        self.num_switch = num_switch
        self.switch_info = {id: [[]] for id in range(num_switch)}
        self.graph = {id: {} for id in range(num_switch)}

        # nb = {id: [] for id in range(num_switch)}
        for i, j, cost in info:
            self.switch_info[i][0].append(j)
            self.switch_info[j][0].append(i)
            self.graph[i][j] = cost
            self.graph[j][i] = cost


    def init_switch(self):
        dead_switches = [*range(self.num_switch)]
        while dead_switches:
            (data, client_addr) = self.server_socket.recvfrom(self.port)
            switch_id = int(data.decode('utf-8'))

            if switch_id in dead_switches:
                dead_switches.remove(switch_id)
                register_request_received(switch_id)
                self.switch_info[switch_id].append(client_addr)

                num_nhb = len(self.switch_info[switch_id][0])
                self.switch_info[switch_id].append([True] * num_nhb)
                # server_socket.sendto(str(switch_id).encode('UTF-8'), client_addr)
                # register_response_sent(switch_id)
        
            print(switch_id, dead_switches)

        print("All switches alive")
            
    def send_respons(self):
        for id in self.switch_info.keys():
            client_addr = self.switch_info[id][1]
            # 1. nhb switchs, 2. alive, 3. port & addr of nbh
            nhb = self.switch_info[id][0]
            alive = self.switch_info[id][2]
            nhb_addr = []
            for i in nhb:
                nhb_addr.append(list(self.switch_info[i][1]))

            msg = str(list(zip(nhb, alive, nhb_addr)))
            self.server_socket.sendto(msg.encode('UTF-8'), client_addr)
            register_response_sent(id)

    def path_config(self, start):
        dist_list = {node: float('inf') for node in self.graph}
        dist_list[start] = 0
        path = {node: [] for node in self.graph}
        path[start] = []
        pq = [(0, start)]  # Priority queue using a heap

        while pq:
            curr_dist, curr_node = heapq.heappop(pq)
            if curr_dist > dist_list[curr_node]:
                continue

            for nhb, cost in self.graph[curr_node].items():
                dist = curr_dist + cost
                if dist < dist_list[nhb]:
                    dist_list[nhb] = dist
                    path[nhb] = deepcopy(path[curr_node])
                    path[nhb].append(nhb)
                    heapq.heappush(pq, (dist, nhb))
        
        return dist_list, path
    
    def routing_update(self):
        self.routing_table = {switch: self.path_config(switch) for switch in self.graph}

        for main_key in self.routing_table.keys():
            msg = ''
            for dist_key in self.routing_table[main_key][0].keys():
                if main_key != dist_key:
                    msg += (f"{main_key},{dist_key}:{self.routing_table[main_key][1][dist_key][0]},{self.routing_table[main_key][0][dist_key]}\n")
                else:
                    msg += (f"{main_key},{dist_key}:{main_key},{self.routing_table[main_key][0][dist_key]}\n")


            client_addr = self.switch_info[main_key][1]
            self.server_socket.sendto(msg.encode('UTF-8'), client_addr)

        routing_table_update(self.routing_table)

def main():
    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 3:
        print ("Usage: python controller.py <port> <config file>\n")
        sys.exit(1)
    print(num_args)

    # Write your code below or elsewhere in this file
    sv = server(int(sys.argv[1]), sys.argv[2])
    sv.init_switch()
    sv.send_respons()
    sv.routing_update()



    
    dist_list, path = sv.path_config(1)


if __name__ == "__main__":
    main()