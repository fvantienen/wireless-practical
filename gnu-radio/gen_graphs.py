#!/usr/bin/env python2
import csv
from optparse import OptionParser
from sklearn.metrics import roc_curve, auc
from scipy.stats import norm
import numpy as np
import matplotlib as mpl
mpl.use('pgf')

# Variables
dvbt_freq = [498, 522, 698, 722, 762] 	# The DVB-T frequencies in Delft
dvbt_width = 7.61						# Width of a DVB-T channel in MHz
random_cnt = 10000						# Amount of random number generated
input_file = "results/detector.csv"		# The input file from the DVB-T detector
output_file_prefix = ""					# Output file prefix for the figures
verbose = True							# Enable debugging information

# Calculate figure size based on LaTex text width
def figsize(scale):
    fig_width_pt = 424.58624                        # Get this from LaTeX using \the\textwidth
    inches_per_pt = 1.0/72.27                       # Convert pt to inch
    golden_mean = (np.sqrt(5.0)-1.0)/2.0            # Aesthetic ratio (you could change this)
    fig_width = fig_width_pt*inches_per_pt*scale    # width in inches
    fig_height = fig_width*golden_mean              # height in inches
    fig_size = [fig_width,fig_height]
    return fig_size

# Set correct settings for LaTex plotting
pgf_with_latex = {                      # setup matplotlib to use latex for output
    "pgf.texsystem": "pdflatex",        # change this if using xetex or lautex
    "text.usetex": True,                # use LaTeX to write all text
    "font.family": "serif",
    "font.serif": [],                   # blank entries should cause plots to inherit fonts from the document
    "font.sans-serif": [],
    "font.monospace": [],
    "axes.labelsize": 10,               # LaTeX default is 10pt font.
    "font.size": 9,
    "legend.fontsize": 8,               # Make the legend/label fonts a little smaller
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.figsize": figsize(0.9),     # default fig size of 0.9 textwidth
    "pgf.preamble": [
        r"\usepackage[utf8x]{inputenc}",    # use utf8 fonts becasue your computer can handle it :)
        r"\usepackage[T1]{fontenc}",        # plots will be generated using this preamble
        ]
    }
mpl.rcParams.update(pgf_with_latex)
import matplotlib.pyplot as plt

# Create a new plot
def new_plot(width):
    plt.clf()
    fig = plt.figure(figsize=figsize(width))
    ax = fig.add_subplot(111)
    return fig, ax

# Save a plot
def save_plot(filename):
    plt.savefig('results/{}.pgf'.format(output_file_prefix + filename))
    plt.savefig('results/{}.pdf'.format(output_file_prefix + filename))

# Print debug information
def print_debug(text):
	if verbose:
		print(text)

# Calculate the statistics
def calc_statistics(meas):
	mean = np.mean(meas)
	std = np.std(meas)
	norm_dist = norm(mean, std)
	rvs = norm_dist.rvs(random_cnt)
	rvs.sort()
	pdf = norm_dist.pdf(rvs)
	cdf = norm_dist.cdf(rvs)
	return (mean, std, rvs, pdf, cdf)

# Find nearest value in array
def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return idx

# Plot an ROC curve
def plot_roc_curve(false_positive_rate, true_positive_rate, filename):
	# Calculate AUC value
	roc_auc = auc(false_positive_rate, true_positive_rate)

	# Generate the plot
	fig, ax = new_plot(0.9)
	#ax.set_title('Receiver Operating Characteristic')
	ax.plot(false_positive_rate, true_positive_rate, 'b', label='AUC = %0.2f'% roc_auc)
	ax.legend(loc='lower right')
	ax.plot([0,1],[0,1],'r--')
	ax.set_xlim([-0.1,1.2])
	ax.set_ylim([-0.1,1.2])
	ax.set_ylabel('True Positive Rate')
	ax.set_xlabel('False Positive Rate')
	save_plot(filename)

# Plot the PDF curve
def plot_pdf_curve(pos_rvs, pos_pdf, neg_rvs, neg_pdf, filename):
	# Generate the plot
	fig, ax = new_plot(0.9)
	ax.plot(pos_rvs, pos_pdf, 'g', label='DVB-T signal')
	ax.plot(neg_rvs, neg_pdf, 'r', label='Noise')
	ax.set_xlim([-90,-60])
	ax.legend(loc='lower right')
	ax.set_ylabel('Probability density')
	ax.set_xlabel('dB')
	save_plot(filename)

	
# Read measurements
def read_measurements():
	# Setup variables
	actual = []
	measurement = []
	positive_meas = []
	negative_meas = []

	# Open the input file
	with open(input_file, 'rb') as in_f:
		reader = csv.reader(in_f)

		# Go trough all the measurements
		for row in reader:

			# Check if this is an actual DVB-T station
			is_dvbt = False
			for freq in dvbt_freq:
				if (freq - dvbt_width/2) < float(row[0]) < (freq + dvbt_width/2):
					is_dvbt = True
					break

			# For the actual ROC curve
			actual.append(is_dvbt)
			measurement.append(float(row[2]))

			# For the random ROC cruve
			if is_dvbt:
				positive_meas.append(float(row[2]))
			else:
				negative_meas.append(float(row[2]))

	# Return information
	return (actual, measurement, positive_meas, negative_meas)

# Generate All the graphs
def gen_graphs():
	# First read measurements
	(actual, measurement, positive_meas, negative_meas) = read_measurements()
	print_debug("Done reading measurements!")

	# Plot the actual ROC curve
	false_positive_rate, true_positive_rate, thresholds = roc_curve(actual, measurement)
	plot_roc_curve(false_positive_rate, true_positive_rate, "roc_real")
	print_debug("Done plotting actual ROC!")

	# Calculate statistics
	(pos_mean, pos_std, pos_rvs, pos_pdf, pos_cdf) = calc_statistics(positive_meas)
	(neg_mean, neg_std, neg_rvs, neg_pdf, neg_cdf) = calc_statistics(negative_meas)

	# Debug information
	print_debug("Statistics")
	print_debug("  Positive mean: %.2f, std: %.2f" % (pos_mean, pos_std))
	print_debug("  Negative mean: %.2f, std: %.2f" % (pos_mean, pos_std))

	# Plot the PDF graph
	plot_pdf_curve(pos_rvs, pos_pdf, neg_rvs, neg_pdf, "pdf")
	print_debug("Done plotting PDF curve!")

	# Calculate the ROC based on statistics
	curve_x = []
	curve_y = []
	for x in np.arange(-85, -65, 0.1):
		curve_x.append(neg_cdf[find_nearest(pos_rvs, x)])
		curve_y.append(pos_cdf[find_nearest(neg_rvs, x)])

	# Plot the ROC curve base on statistics
	plot_roc_curve(curve_x, curve_y, "roc_norm")
	print_debug("Done plotting normal distributed ROC!")


# Main function
if __name__ == '__main__':
	# Setup the option parser
	parser = OptionParser()
	parser.add_option("-q",
		dest="verbose", action="store_false", default=verbose, help="Disables debugging information (quiet mode)")
	parser.add_option("--dvbt_width",
		dest="dvbt_width", type="float", default=dvbt_width, help="The DVB-T channel width in MHz")
	parser.add_option("--random_cnt",
		dest="random_cnt", type="int", default=random_cnt, help="Amount of random number generated for the Normal distributions")
	parser.add_option("-i", "--input_file",
		dest="input_file", type="string", default=input_file, help="The input file from the DVB-T detector")
	parser.add_option("-o", "--output_file_prefix",
		dest="output_file_prefix", type="string", default=output_file_prefix, help="The output file prefix for the figures")

	# Parse the options
	(options, args) = parser.parse_args()
	verbose = options.verbose
	dvbt_width = options.dvbt_width
	random_cnt = options.random_cnt
	input_file = options.input_file
	output_file_prefix = options.output_file_prefix

	# Run all the graphs
	gen_graphs()