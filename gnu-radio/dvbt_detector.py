#!/usr/bin/env python2
from optparse import OptionParser
from dvbt_scanner import dvbt_scanner
import thread
import time

# Variables
freq_min = 480		# Frequency minimum in MHz
freq_max = 800  	# Frequency maximum in MHz
freq_step = 0.5		# Frequency steps in MHz
threshold = -77		# Detection threshold level in dB
wait_time = 4		# Wait time in seconds between frequency change
output_file = "results/detector.csv"	# The output file for the results
verbose = True 		# Show debugging information

# Print debug information
def print_debug(text):
	if verbose:
		print(text)

# Main detector
def detector(scanner):
	# Output debug information
	est_time = (freq_max - freq_min) / freq_step * wait_time / 60;
	print_debug("")
	print_debug("=====================================================================================")
	print_debug("Starting detector with %.2fdB threshold from %.2fMHz to %.2fMHz (with step %.2fMHz)." % (threshold, freq_min, freq_max, freq_step))
	print_debug("Estimated time is %.2f minutes (based on wait time of %d seconds)" % (est_time, wait_time))
	print_debug("=====================================================================================")
	print_debug("")

	# Open the output file
	f = open(output_file, "w")

	# Set the detection level
	scanner.set_threshold(threshold)

	# Go trough the frequencies
	for freq in range(int(freq_min*1e6), int(freq_max*1e6), int(freq_step*1e6)):
		# Set the frequency
		scanner.set_freq(freq)

		# Wait for some time
		time.sleep(wait_time)

		# Do the measurement
		freq_mhz = freq / 1e6
		signal_level = scanner.get_signal_level()
		detected = scanner.get_detected()
		f.write("%.2f,%.2f,%.2f,%d\n" % (freq_mhz, threshold, signal_level, detected))

		# Print debug information
		print_debug("Freq: %.2fMHz, Signal level: %.2fdB, Detected %d" % (freq_mhz, signal_level, detected))

	# Close the output file
	f.close()

	# Output debug information
	print_debug("")
	print_debug("=====================================================================================")
	print_debug("FINISHED")
	print_debug("=====================================================================================")
	print_debug("")

# Main function
if __name__ == '__main__':
	# Make sure GNURadio works
	import ctypes
	import sys
	if sys.platform.startswith('linux'):
		try:
			x11 = ctypes.cdll.LoadLibrary('libX11.so')
			x11.XInitThreads()
		except:
			print "Warning: failed to XInitThreads()"

	# Setup the option parser
	parser = OptionParser()
	parser.add_option("-q",
		dest="verbose", action="store_false", default=verbose, help="Disables debugging information (quiet mode)")
	parser.add_option("--freq_min",
		dest="freq_min", type="float", default=freq_min, help="The minimum frequency to search from in MHz")
	parser.add_option("--freq_max",
		dest="freq_max", type="float", default=freq_max, help="The maximum frequency to search from in MHz")
	parser.add_option("--freq_step",
		dest="freq_step", type="float", default=freq_step, help="The frequency steps to take while searching in MHz")
	parser.add_option("--threshold",
		dest="threshold", type="float", default=threshold, help="Threshold in dB used for the detector")
	parser.add_option("--wait_time",
		dest="wait_time", type="float", default=wait_time, help="Amount of time to wait between fequency steps in seconds")
	parser.add_option("-o", "--output_file",
		dest="output_file", type="string", default=output_file, help="The output file for the CSV data")

	# Parse the options
	(options, args) = parser.parse_args()
	verbose = options.verbose
	freq_min = options.freq_min
	freq_max = options.freq_max
	freq_step = options.freq_step
	threshold = options.threshold
	wait_time = options.wait_time
	output_file = options.output_file

	# Start the scanner
	scanner = dvbt_scanner()
	scanner.Start(True)

	# Start the detector
	thread.start_new_thread(detector, (scanner,))

	# Wait for the scanner to close
	scanner.Wait()
	thread.exit()
	sys.exit(0);