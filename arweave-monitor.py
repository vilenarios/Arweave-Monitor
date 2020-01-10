#!/usr/bin/python3.8
# Python3.8 is the primary prerequisite for runnig this script effectively
# This script must be placed in the root of the arweave directory.
# sudo apt update
# sudo apt install software-properties-common
# sudo add-apt-repository ppa:deadsnakes/ppa
# sudo apt install python3.8 -y
# sudo apt install python3.8-dev -y
# sudo apt install python3-pip -y
# sudo python3.8 -m pip install requests
# sudo python3.8 -m pip install psutil

import glob
import requests
import json
import sys, os
import re
import subprocess
from datetime import datetime, date
import time
import socket
import math
import shutil
import psutil

def toFixed(numObj, digits=0):
	return f"{numObj:.{digits}f}"

# Update to your graphite server IP and Port
# If graphite is not being used, leave this at xx.xx.xx.xx
graphite_server_ip = 'xx.xx.xx.xx'
# Default graphite port
graphite_server_port = 2003

# Setup some variables
old_total_bytes = 0
starttime = time.time()
ipv4_addr = requests.get('http://ip.42.pl/raw').text
friendly_name = (socket.gethostname())

# Get and set arweave directory and log locations
get_arweave_directory = 'locate arweave-monitor.py'
get_arweave_directory = subprocess.check_output(get_arweave_directory, shell=True)
arweave_directory = get_arweave_directory.split()
arweave_directory = arweave_directory[0].decode("utf-8").strip()
arweave_directory = arweave_directory.replace('arweave-monitor.py','')
arweave_logs = arweave_directory + 'logs/*'

# Get latest log file
all_log_files = glob.glob(arweave_logs)
latest_log_file = max(all_log_files, key=os.path.getctime)

oldest_log_file = min(all_log_files, key=os.path.getctime)
oldest_log_file = oldest_log_file.split("_")
oldest_date = oldest_log_file[1].split("-")
d1 = date(int(oldest_date[0]), int(oldest_date[1]), int(oldest_date[2]))
d2 = date.today()
days_of_logs = abs(d2-d1).days

# Finalize variables
get_node_port = 'cat %s | grep port' % (latest_log_file)
get_node_port = subprocess.check_output(get_node_port, shell=True)
node_port = get_node_port.split()
node_port = node_port[1].decode("utf-8").strip()

get_node_wallet = 'cat %s | grep mining_address:' % (latest_log_file)
get_node_wallet= subprocess.check_output(get_node_wallet, shell=True)
my_wallet= get_node_wallet.split()
my_wallet = my_wallet[1].decode("utf-8").strip()
my_wallet = my_wallet.replace('"','')

node_public_ip = 'http://' + ipv4_addr + ':' + node_port
node_private_ip = 'http://127.0.0.1:' + node_port
node_wallet = node_private_ip + '/wallet/' + my_wallet + '/balance'
node_metrics = node_private_ip + '/metrics'
node_peers = node_private_ip + '/peers'


def send_msg(message):
	# print ('sending message: ', message.strip())
	# If you do not use graphite, and the IP is set to xx.xx.xx.xx then the below will be skipped and you will only receive messages locally
	try:
		if graphite_server_ip != 'xx.xx.xx.xx':
			sock = socket.socket()
			sock.connect((graphite_server_ip, graphite_server_port))
			sock.sendall(message.encode())
			sock.close()
	except:
		print (graphite_server_ip, "is down!")

print("=========================================================================")
print("Arweave node monitor by @vilenarios")
print("Sending data to Graphite/Grafana at " + graphite_server_ip + ":" + str(graphite_server_port))
print("=========================================================================")

while True:
	try:
		# Reporting on core node information
		print("-----------------------------Core----------------------------------------")
		node_info = json.loads(requests.get(node_private_ip).text)
		node_balance = requests.get(node_wallet)
		node_all_metrics = requests.get(node_metrics)
		node_all_metrics = node_all_metrics.content.decode('utf-8')
	
		print("Friendly Name:", friendly_name)
		print("Public IP:", node_public_ip)
		print("Release:", node_info['release'])

		print("Current Block:", node_info['current'])
		message = "%s.CurrentBlock %s %d\n" % (friendly_name, node_info['current'], int(time.time()))
		send_msg(message)

		# Start sending messages to Graphite
		print("Current Height:", node_info['height'])
		message = "%s.Height %s %d\n" % (friendly_name, node_info['height'], int(time.time()))
		send_msg(message)

		# Get latest block and calculate difficulty
		node_height = node_private_ip + '/block/height/' + str(node_info['height'])
		latest_block = json.loads(requests.get(node_height).text)
		large_difficulty = int(latest_block['diff'])
		small_difficulty = math.log2((2**256) / ((2**256) - large_difficulty))
		print ("Last Block Difficulty:", round(small_difficulty,3))
		message = "%s.Difficulty %s %d\n" % (friendly_name, round(small_difficulty,3), int(time.time()))
		send_msg(message)

		block_size = (latest_block['block_size'])
		print ("Size of last block:", block_size)
		message = "%s.BlockSize %s %d\n" % (friendly_name, latest_block['block_size'], int(time.time()))
		send_msg(message)

		weave_size = (latest_block['weave_size'])
		print ("Current Weave Size:", weave_size)
		message = "%s.WeaveSize %s %d\n" % (friendly_name, latest_block['weave_size'], int(time.time()))
		send_msg(message)

		# Get number of txs for last block
		txs_amount = (latest_block['txs'])
		print ("Txs for last block:", len(txs_amount))
		message = "%s.LastBlockTxs %s %d\n" % (friendly_name, len(txs_amount), int(time.time()))
		send_msg(message)

		print("Blocks:", node_info['blocks'])
		message = "%s.Blocks %s %d\n" % (friendly_name, node_info['blocks'], int(time.time()))
		send_msg(message)

		# Get all peers and separate top 5
		print("Peers:", node_info['peers'])
		message = "%s.Peers.Total %s %d\n" % (friendly_name, node_info['peers'], int(time.time()))
		send_msg(message)

		node_all_peers = requests.get(node_peers)
		node_all_peers = node_all_peers.content.decode('utf-8')
		node_all_peers = node_all_peers.replace('[','')
		node_all_peers = node_all_peers.replace('"','')
		node_all_peers = node_all_peers.split(",")
		top_5_peers = '"' + node_all_peers[0] + ',' + node_all_peers[1] + ',' + node_all_peers[2] + ',' + node_all_peers[3] + ',' + node_all_peers[4] + '"'
		print("My top 5 peers:", top_5_peers)
		message = "%s.Peers.Top_5 %s %d\n" % (friendly_name, top_5_peers, int(time.time()))
		send_msg(message)

		print("Latency:", node_info['node_state_latency']/1000, "ms")
		message = "%s.Latency %s %d\n" % (friendly_name, node_info['node_state_latency']/1000, int(time.time()))
		send_msg(message)
		
		print("Wallet:", my_wallet)
		print("Balance:", toFixed(node_balance.json()/1000000000000,5), "AR")
		message = "%s.WalletBalance %s %d\n" % (friendly_name, toFixed(node_balance.json()/1000000000000,5), int(time.time()))
		send_msg(message)

		# Reporting on metrics
		print("-----------------------------Metrics-------------------------------------")
		match = re.findall(r'process_io_pagefaults_total [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("Process_io_pagefaults_total:", splitstring[1])
			message = "%s.Metrics.Process_io_pagefaults_total %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)
	
		match = re.findall(r'process_uptime_seconds [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("process_uptime_seconds:", splitstring[1])
			message = "%s.Metrics.process_uptime_seconds %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)
	
		match = re.findall(r'process_disk_reads_total [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("process_disk_reads_total:", splitstring[1])
			message = "%s.Metrics.process_disk_reads_total %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)
	
		match = re.findall(r'process_disk_writes_total [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("process_disk_writes_total:", splitstring[1])
			message = "%s.Metrics.process_disk_writes_total %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)
	
		match = re.findall(r'erlang_vm_memory_processes_bytes_total{usage="used"} [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("erlang_vm_memory_processes_bytes_total{usage=used}:", splitstring[1])
			message = "%s.Metrics.Erlang_vm_memory_processes_bytes_total_used %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)
	
		match = re.findall(r'erlang_vm_statistics_bytes_output_total [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("erlang_vm_statistics_bytes_output_total:", splitstring[1])
			message = "%s.Metrics.erlang_vm_statistics_bytes_output_total %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)
	
		match = re.findall(r'erlang_vm_statistics_bytes_received_total [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("erlang_vm_statistics_bytes_received_total:", splitstring[1])
			message = "%s.Metrics.erlang_vm_statistics_bytes_received_total %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)
	
		match = re.findall(r'erlang_vm_port_count [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("erlang_vm_port_count:", splitstring[1])
			message = "%s.Metrics.erlang_vm_port_count %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)

		match = re.findall(r'process_open_fds [0-9]+', node_all_metrics)
		if match:
			splitstring = match[0].split()
			print ("process_open_fds:", splitstring[1])
			message = "%s.Metrics.process_open_fds %s %d\n" % (friendly_name, splitstring[1], int(time.time()))
			send_msg(message)

		try:
			check_tx_bytes_per_second = 'tac %s | grep "bytes_per_second" -m1' % (latest_log_file)
			tx_bytes_per_second = subprocess.check_output(check_tx_bytes_per_second, shell=True)
			splitstring = tx_bytes_per_second.split()
			print ("tx_bytes_per_second:", splitstring[1].decode("utf-8"))
			message = "%s.Metrics.tx_bytes_per_second %s %d\n" % (friendly_name, splitstring[1].decode("utf-8"), int(time.time()))
		except:
			print ("tx_bytes_per_second: 0")
			message = "%s.Metrics.tx_bytes_per_second 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			check_hash = 'tac %s | grep "miner_hashes_per_second" -m1' % (latest_log_file)
			miner_hashes_per_second = subprocess.check_output(check_hash, shell=True)
			splitstring = miner_hashes_per_second.split()
			print ("miner_hashes_per_second:", splitstring[1].decode("utf-8"))
			message = "%s.Metrics.miner_hashes_per_second %s %d\n" % (friendly_name, splitstring[1].decode("utf-8"), int(time.time()))
		except:
			print ("miner_hashes_per_second: 0")
			message = "%s.Metrics.miner_hashes_per_second 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		# Calculate Total Network H/S
		network_hash_per_second = ((2**256) / ((2**256) - large_difficulty)) / 125
		print ("Total Network Hash per Second:", round(network_hash_per_second,1))
		message = "%s.Network_hash_per_second %s %d\n" % (friendly_name, round(network_hash_per_second,1), int(time.time()))
		send_msg(message) 

		# Calculate chances of finding a block (luck) purely based on hashrate only, and does not take disk/network into account.
		float(splitstring[1])
		chance_to_find = 120 * (network_hash_per_second / float(splitstring[1]))
		print ("Your Luck is one block every", round((chance_to_find / 60 / 60),3), "hours")
		message = "%s.Metrics.Luck %s %d\n" % (friendly_name, round((chance_to_find / 60 / 60),3), int(time.time()))
		send_msg(message)

		# Determine if any blocks have been found
		try:
			get_stage2_count = "cat %s | grep 'Stage 2/3' -c" % (arweave_logs)
			get_stage2_count = subprocess.check_output(get_stage2_count, shell=True)
			stage2_count = get_stage2_count.decode("utf-8").strip()
			blocks_submitted_per_day = int(stage2_count) / days_of_logs
			print ("Blocks submitted per day:", blocks_submitted_per_day)
			message = "%s.Logs.Blocks_Submitted_Per_day %s %d\n" % (friendly_name, blocks_submitted_per_day, int(time.time()))
		except:
			print ("Blocks submitted per day: 0")
			message = "%s.Logs.Blocks_Submitted_Per_day 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			blocks_submitted = 'tac %s | grep "Stage 2/3" -c' % (latest_log_file)
			blocks_submitted_count = subprocess.check_output(blocks_submitted, shell=True)
			print ("Blocks submitted to the network this session:", blocks_submitted_count.decode("utf-8").strip())
			message = "%s.Logs.Blocks_submitted %s %d\n" % (friendly_name, blocks_submitted_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("Blocks submitted this session: 0")
			message = "%s.Logs.Blocks_Submitted 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)
		
		try:
			get_stage3_count = "cat %s | grep 'Stage 3/3' -c" % (arweave_logs)
			get_stage3_count = subprocess.check_output(get_stage3_count, shell=True)
			stage3_count = get_stage3_count.decode("utf-8").strip()
			blocks_found_per_day = int(stage3_count) / days_of_logs
			print ("Blocks found per day:", blocks_found_per_day)
			message = "%s.Logs.Blocks_Found_Per_day %s %d\n" % (friendly_name, blocks_found_per_day, int(time.time()))
		except:
			print ("Blocks found per day: 0")
			message = "%s.Logs.Blocks_Found_Per_day 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			blocks_found = 'tac %s | grep "Stage 3/3" -c' % (latest_log_file)
			blocks_found_count = subprocess.check_output(blocks_found, shell=True)
			print ("Blocks found this session:", blocks_found_count.decode("utf-8").strip())
			message = "%s.Logs.Blocks_Found %s %d\n" % (friendly_name, blocks_found_count.decode("utf-8").strip(), int(time.time()))

		except:
			print ("Blocks found this session: 0")
			message = "%s.Logs.Blocks_Found 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			blocks_found_ratio = blocks_found_per_day / blocks_submitted_per_day
			print ("Blocks found/submitted ratio:", blocks_found_ratio)
			message = "%s.Logs.Blocks_Found_Ratio %s %d\n" % (friendly_name, blocks_found_ratio, int(time.time()))
		except:
			print ("Blocks found/submitted ratio: 0")
			message = "%s.Logs.Blocks_Found_Ratio 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)
		
		# Specific disk metrics
		total, used, free = shutil.disk_usage(arweave_directory)
		print("Total Arweave Disk: %d GB" % (total // (2**30)))
		message = "%s.Metrics.Disk.TotalGB %s %d\n" % (friendly_name, (total // (2**30)), int(time.time()))
		send_msg(message)
		print("Used Arweave Disk: %d GB" % (used // (2**30)))
		message = "%s.Metrics.Disk.UsedGB %s %d\n" % (friendly_name, (used // (2**30)), int(time.time()))
		send_msg(message)
		print("Free Arweave Disk: %d GB" % (free // (2**30)))
		message = "%s.Metrics.Disk.FreeGB %s %d\n" % (friendly_name, (free // (2**30)), int(time.time()))
		send_msg(message)

		# Specific CPU metrics
		try:
			cpu_usage = psutil.cpu_percent()
			print("Average CPU Thread Usage: %d percent" % cpu_usage)
			message = "%s.Metrics.CPU_Usage %s %d\n" % (friendly_name, cpu_usage, int(time.time()))
			send_msg(message)
		except:
			print("CPU capture failed.  Is psutil installed properly?")

		# Get CPU temp WORK IN PROGRESS
		try:
			average_temp = 0
			core_count = 0
			cpu_temps = psutil.sensors_temperatures()
			for name, entries in cpu_temps.items():
				for entry in entries:
					if "Package id" in entry.label:
						average_cpu_temp = entry.current
						print("Average CPU Temp on all cores: %d °C" % average_cpu_temp)
						message = "%s.Metrics.CPU_Avg_Temp %s %d\n" % (friendly_name, average_cpu_temp, int(time.time()))
						send_msg(message)
						break

		except:
			print("CPU temperature capture failed.  Is psutil installed properly?")

		# Specific RAM metrics
		try:
			memory = psutil.virtual_memory()
			print("Total Node Memory: %d MB" % (memory.total / 1000000))
			message = "%s.Metrics.RAM.TotalMB %s %d\n" % (friendly_name, (memory.total / 1000000), int(time.time()))
			send_msg(message)
			print("Used Node Memory: %d MB" % (memory.used / 1000000))
			message = "%s.Metrics.RAM.UsedMB %s %d\n" % (friendly_name, (memory.used / 1000000), int(time.time()))
			send_msg(message)
			free = memory.total - memory.used
			print("Free Node Memory: %d MB" % (free / 1000000))
			message = "%s.Metrics.RAM.FreeMB %s %d\n" % (friendly_name, (free / 1000000), int(time.time()))
			send_msg(message)
		except:
			print("Memory capture failed.  Is psutil installed properly?")

		# Specific network metrics
		open_connections = 'netstat -an | wc -l'
		open_connections_count = subprocess.check_output(open_connections, shell=True)
		print ("Open network connections:", open_connections_count.decode("utf-8").strip())
		message = "%s.Metrics.Open_Connections %s %d\n" % (friendly_name, open_connections_count.decode("utf-8").strip(), int(time.time()))
		send_msg(message)

		try:
			bytes_sent = psutil.net_io_counters().bytes_sent
			print ("Bytes Sent:", bytes_sent)
			message = "%s.Metrics.Bytes_Sent %s %d\n" % (friendly_name, bytes_sent, int(time.time()))
			send_msg(message)

			bytes_received = psutil.net_io_counters().bytes_recv
			print ("Bytes Received:", bytes_received)
			message = "%s.Metrics.Bytes_Received %s %d\n" % (friendly_name, bytes_received, int(time.time()))
			send_msg(message)

			# Calucate bits/second
			new_total_bytes = bytes_received + bytes_sent
			if old_total_bytes:
				bits_per_second = ((new_total_bytes - old_total_bytes)*8)/60 # calculate bits/sec, since this script runs every minute
				print ("Bits per Second:", bits_per_second)
				message = "%s.Metrics.BitsPerSecond %s %d\n" % (friendly_name, bits_per_second, int(time.time()))
				send_msg(message)
			old_total_bytes = new_total_bytes
		except:
			print("Bits per second capture failed.  Is psutil installed properly?")

		# Collect logs of interest including forks, errors
		print("-----------------------------Logs----------------------------------------")
		try:
			started_fork_recovery_proc = 'tac %s | grep "started_fork_recovery_proc" -c' % (latest_log_file)
			started_fork_recovery_proc_count = subprocess.check_output(started_fork_recovery_proc, shell=True)
			print ("started_fork_recovery_proc_count:", started_fork_recovery_proc_count.decode("utf-8").strip())
			message = "%s.Logs.Forks.started_fork_recovery_proc_count %s %d\n" % (friendly_name, started_fork_recovery_proc_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("started_fork_recovery_proc_count: 0")
			message = "%s.Logs.Forks.started_fork_recovery_proc_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			fork_recovered_successfully = 'tac %s | grep "fork_recovered_successfully" -c' % (latest_log_file)
			fork_recovered_successfully_count = subprocess.check_output(fork_recovered_successfully, shell=True)
			print ("fork_recovered_successfully_count", fork_recovered_successfully_count.decode("utf-8").strip())
			message = "%s.Logs.Forks.fork_recovered_successfully_count %s %d\n" % (friendly_name, fork_recovered_successfully_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("fork_recovered_successfully_count: 0")
			message = "%s.Logs.Forks.fork_recovered_successfully_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			applying_fork_recovery = 'tac %s | grep "applying_fork_recovery" -c' % (latest_log_file)
			applying_fork_recovery_count = subprocess.check_output(applying_fork_recovery, shell=True)
			print ("applying_fork_recovery_count:", applying_fork_recovery_count.decode("utf-8").strip())
			message = "%s.Logs.Forks.applying_fork_recovery_count %s %d\n" % (friendly_name, applying_fork_recovery_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("applying_fork_recovery_count: 0")
			message = "%s.Logs.Forks.applying_fork_recovery_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			applied_fork_recovery_block = 'tac %s | grep "applied_fork_recovery_block" -c' % (latest_log_file)
			applied_fork_recovery_block_count = subprocess.check_output(applied_fork_recovery_block, shell=True)
			print ("applied_fork_recovery_block_count:", applied_fork_recovery_block_count.decode("utf-8").strip())
			message = "%s.Logs.Forks.applied_fork_recovery_block_count %s %d\n" % (friendly_name, applied_fork_recovery_block_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("applied_fork_recovery_block_count: 0")
			message = "%s.Logs.Forks.applied_fork_recovery_block_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			encountered_block_on_same_fork_as_recovery_process = 'tac %s | grep "encountered_block_on_same_fork_as_recovery_process" -c' % (latest_log_file)
			encountered_block_on_same_fork_as_recovery_process_count = subprocess.check_output(encountered_block_on_same_fork_as_recovery_process, shell=True)
			print ("encountered_block_on_same_fork_as_recovery_process_count:", encountered_block_on_same_fork_as_recovery_process_count.decode("utf-8").strip())
			message = "%s.Logs.Forks.encountered_block_on_same_fork_as_recovery_process_count %s %d\n" % (friendly_name, encountered_block_on_same_fork_as_recovery_process_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("encountered_block_on_same_fork_as_recovery_process_count: 0")
			message = "%s.Logs.Forks.encountered_block_on_same_fork_as_recovery_process_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			updating_fork_recovery_target = 'tac %s | grep "updating_fork_recovery_target" -c' % (latest_log_file)
			updating_fork_recovery_target_count = subprocess.check_output(updating_fork_recovery_target, shell=True)
			print ("updating_fork_recovery_target_count:", updating_fork_recovery_target_count.decode("utf-8").strip())
			message = "%s.Logs.Forks.updating_fork_recovery_target_count %s %d\n" % (friendly_name, updating_fork_recovery_target_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("updating_fork_recovery_target_count: 0")
			message = "%s.Logs.Forks.updating_fork_recovery_target_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			fork_recovered_successfully = 'tac %s | grep "fork_recovered_successfully" -c' % (latest_log_file)
			fork_recovered_successfully_count = subprocess.check_output(fork_recovered_successfully, shell=True)
			print ("fork_recovered_successfully_count:", fork_recovered_successfully_count.decode("utf-8").strip())
			message = "%s.Logs.Forks.fork_recovered_successfully_count %s %d\n" % (friendly_name, fork_recovered_successfully_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("fork_recovered_successfully_count: 0")
			message = "%s.Logs.Forks.fork_recovered_successfully_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			encountered_block_on_different_fork_to_recovery_process = 'tac %s | grep "encountered_block_on_different_fork_to_recovery_process" -c' % (latest_log_file)
			encountered_block_on_different_fork_to_recovery_process_count = subprocess.check_output(encountered_block_on_different_fork_to_recovery_process, shell=True)
			print ("encountered_block_on_different_fork_to_recovery_process_count:", encountered_block_on_different_fork_to_recovery_process_count.decode("utf-8").strip())
			message = "%s.Logs.Forks.encountered_block_on_different_fork_to_recovery_process_count %s %d\n" % (friendly_name, encountered_block_on_different_fork_to_recovery_process_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("encountered_block_on_different_fork_to_recovery_process_count: 0")
			message = "%s.Logs.Forks.encountered_block_on_different_fork_to_recovery_process_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			no_foreign_blocks_found = 'tac %s | grep "no foreign blocks found" -c' % (latest_log_file)
			no_foreign_blocks_found_count = subprocess.check_output(no_foreign_blocks_found, shell=True)
			print ("no_foreign_blocks_found_count:", no_foreign_blocks_found_count.decode("utf-8").strip())
			message = "%s.Logs.Errors.no_foreign_blocks_found_count %s %d\n" % (friendly_name, no_foreign_blocks_found_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("no_foreign_blocks_found_count: 0")
			message = "%s.Logs.Errors.no_foreign_blocks_found_count 0 %d\n" % (friendly_name, int(time.time()))			
		send_msg(message)

		try:
			error_report = 'tac %s | grep "ERROR REPORT" -c' % (latest_log_file)
			error_report_count = subprocess.check_output(error_report, shell=True)
			print ("error_report_count:", error_report_count.decode("utf-8").strip())
			message = "%s.Logs.Errors.error_report_count %s %d\n" % (friendly_name, error_report_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("error_report_count: 0")
			message = "%s.Logs.Errors.error_report_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			init_randomx_hashing = 'tac %s | grep "Initialising RandomX dataset for fast hashing." -c' % (latest_log_file)
			init_randomx_hashing_count = subprocess.check_output(init_randomx_hashing, shell=True)
			print ("init_randomx_hashing_count:", init_randomx_hashing_count.decode("utf-8").strip())
			message = "%s.Logs.Info.init_randomx_hashing_count %s %d\n" % (friendly_name, init_randomx_hashing_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("init_randomx_hashing_count: 0")
			message = "%s.Logs.Info.init_randomx_hashing_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			unexpected_tx_response_timeout = 'tac %s | grep "unexpected_tx_response: {error,connect_timeout}" -c' % (latest_log_file)
			unexpected_tx_response_timeout_count = subprocess.check_output(unexpected_tx_response_timeout, shell=True)
			print ("unexpected_tx_response_timeout_count:", unexpected_tx_response_timeout_count.decode("utf-8").strip())
			message = "%s.Logs.Warning.unexpected_tx_response_timeout_count %s %d\n" % (friendly_name, unexpected_tx_response_timeout_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("unexpected_tx_response_timeout_count: 0")
			message = "%s.Logs.Warning.unexpected_tx_response_timeout_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			unexpected_tx_response_econnrefused = 'tac %s | grep "unexpected_tx_response: {error,econnrefused}" -c' % (latest_log_file)
			unexpected_tx_response_econnrefused_count = subprocess.check_output(unexpected_tx_response_econnrefused, shell=True)
			print ("unexpected_tx_response_econnrefused_count:", unexpected_tx_response_econnrefused_count.decode("utf-8").strip())
			message = "%s.Logs.Warning.unexpected_tx_response_econnrefused_count %s %d\n" % (friendly_name, unexpected_tx_response_econnrefused_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("unexpected_tx_response_econnrefused_count: 0")
			message = "%s.Logs.Warning.unexpected_tx_response_econnrefused_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			sqlite3_warning_long_query = 'tac %s | grep "ar_sqlite3: long_query" -c' % (latest_log_file)
			sqlite3_warning_long_query_count = subprocess.check_output(sqlite3_warning_long_query, shell=True)
			print ("sqlite3_warning_long_query_count:", sqlite3_warning_long_query_count.decode("utf-8").strip())
			message = "%s.Logs.Warning.sqlite3_warning_long_query_count %s %d\n" % (friendly_name, sqlite3_warning_long_query_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("sqlite3_warning_long_query_count: 0")
			message = "%s.Logs.Warning.sqlite3_warning_long_query_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			slow_data_segment_generation = 'tac %s | grep "slow_data_segment_generation" -c' % (latest_log_file)
			slow_data_segment_generation_count = subprocess.check_output(slow_data_segment_generation, shell=True)
			print ("slow_data_segment_generation_count:", slow_data_segment_generation_count.decode("utf-8").strip())
			message = "%s.Logs.Warning.slow_data_segment_generation_count %s %d\n" % (friendly_name, slow_data_segment_generation_count.decode("utf-8").strip(), int(time.time()))
		except:
			print ("slow_data_segment_generation_count: 0")
			message = "%s.Logs.Warning.slow_data_segment_generation_count 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		try:
			check_sqlite3_long_query_microseconds = 'tac %s | grep "microseconds:" -m1' % (latest_log_file)
			sqlite3_long_query_microseconds = subprocess.check_output(check_sqlite3_long_query_microseconds, shell=True)
			splitstring = sqlite3_long_query_microseconds.split()
			print ("sqlite3_long_query_microseconds:", splitstring[1].decode("utf-8"))
			message = "%s.Metrics.sqlite3_long_query_microseconds %s %d\n" % (friendly_name, splitstring[1].decode("utf-8"), int(time.time()))
		except:
			print ("tx_sqlite3_long_query_microseconds: 0")
			message = "%s.Metrics.sqlite3_long_query_microseconds 0 %d\n" % (friendly_name, int(time.time()))
		send_msg(message)

		print("-------------------------------------------------------------------------")

	except Exception as e:
		print (e)
		print ("Error collecting data")

	update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	print("Last update:", update)
	time.sleep(60.0 - ((time.time() - starttime) % 60.0))

	# Update log file location in case arweave-server has been restarted but arweave-monitoring still runs
	# Get latest log file
	all_log_files = glob.glob(arweave_logs)
	latest_log_file = max(all_log_files, key=os.path.getctime)

	oldest_log_file = min(all_log_files, key=os.path.getctime)
	oldest_log_file = oldest_log_file.split("_")
	oldest_date = oldest_log_file[1].split("-")
	d1 = date(int(oldest_date[0]), int(oldest_date[1]), int(oldest_date[2]))
	d2 = date.today()
	days_of_logs = abs(d2-d1).days