# Python
PYTHON = python3

# Paths to student scripts
SENDER_PATH = "sender.py"
RECEIVER_PATH = "receiver.py"
EMULATOR_PATH = "emulator.py"

SENDER_PATH_V1 = "sender_interim.py"
RECEIVER_PATH_V1 = "receiver_interim.py"

SENDER_PATH_V2 = "sender_wo_NACK.py"
RECEIVER_PATH_V2 = "receiver_wo_NACK.py"

SENDER_PATH_V3 = "sender_wo_pid.py"
RECEIVER_PATH_V3 = "receiver_wo_pid.py"

# Ports to clear
# These ports are currently hardcoded in the config file. 
# If you modify the ports in config file they should be changed here as well. 
SENDER_PORT = 8001
RECEIVER_PORT = 8002
EMULATOR_PORT = 8000

# Runs the sender
run-sender:
	-kill -9 $$(lsof -t -i:$(SENDER_PORT))
	$(PYTHON) $(SENDER_PATH) "$(config)"

# Runs the receiver
run-receiver:
	-kill -9 $$(lsof -t -i:$(RECEIVER_PORT))
	$(PYTHON) $(RECEIVER_PATH) "$(config)"

run-emulator:
	-kill -9 $$(lsof -t -i:$(EMULATOR_PORT))
	$(PYTHON) $(EMULATOR_PATH) "$(config)"

# Runs the sender
run-sender-v1:
	-kill -9 $$(lsof -t -i:$(SENDER_PORT))
	$(PYTHON) $(SENDER_PATH_V1) "$(config)"

# Runs the receiver
run-receiver-v1:
	-kill -9 $$(lsof -t -i:$(RECEIVER_PORT))
	$(PYTHON) $(RECEIVER_PATH_V1) "$(config)"

# Runs the sender
run-sender-v2:
	-kill -9 $$(lsof -t -i:$(SENDER_PORT))
	$(PYTHON) $(SENDER_PATH_V2) "$(config)"

# Runs the receiver
run-receiver-v2:
	-kill -9 $$(lsof -t -i:$(RECEIVER_PORT))
	$(PYTHON) $(RECEIVER_PATH_V2) "$(config)"

# Runs the sender
run-sender-v3:
	-kill -9 $$(lsof -t -i:$(SENDER_PORT))
	$(PYTHON) $(SENDER_PATH_V3) "$(config)"

# Runs the receiver
run-receiver-v3:
	-kill -9 $$(lsof -t -i:$(RECEIVER_PORT))
	$(PYTHON) $(RECEIVER_PATH_V3) "$(config)"
