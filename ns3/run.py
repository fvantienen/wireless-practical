#!/usr/bin/env python
import subprocess

# Variables
waf_dir = '../../'			# Folder where the WAF executable exists
scratch_dir = 'practical'	# Folder in which this project sits in the scratch folder
max_processes = 4 			# Maximum number of parallel processes
processes = []				# To keep track of the processess
data_rates = ['5Mbps', '2Mbps', '1Mbps', '500Kbps', '100Kbps']	# Different data rates for simulation
packet_sizes = [512, 1024]										# Different packet sizes for simulation

# Calculate some file paths
build_path = waf_dir + 'waf --run="'  + scratch_dir + '"'
run_path = waf_dir + 'build/scratch/' + scratch_dir + '/' + scratch_dir

# Add a run in parallel if possible else wait for free process
def addRun(run, stas, data_rate, packet_size):
	# Wait and close a specific process
	while len(processes) >= max_processes:
		for proc in processes:
			if proc.poll() is not None:
				if proc.returncode != 0:
					print 'Some run failed!'
				processes.remove(proc)

	# Execute the process
	print("Starting run %d with stas: %d, dr: %s, ps: %d" % (run, stas, data_rate, packet_size))
	run_str = [run_path]
	run_str.append('--run=' + str(run))
	run_str.append('--stas=' + str(stas))
	run_str.append('--dr=' + str(data_rate))
	run_str.append('--ps=' + str(packet_size))
	run_str.append('--of=results/' + str(packet_size) + "_" + str(data_rate) + '.csv')
	processes.append(subprocess.Popen(run_str, shell=False, stdout=subprocess.PIPE));


# First we need to build the program (Call this sync)
subprocess.call(build_path, shell=True)

print("Now starting tests....")

# Now lets build our test set
for packet_size in packet_sizes:
	for data_rate in data_rates:
		for stas in range(1, 40):
			for run in range(0, 5):
				addRun(run, stas, data_rate, packet_size)

# Wait for all the results...
for proc in processes:
	proc.wait()

# Check return codes for success
if any(proc.returncode != 0 for proc in processes):
	print 'Some run failed!'

print("Done with tests!")