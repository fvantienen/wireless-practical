#!/usr/bin/env python2
import csv
import numpy as np
import matplotlib as mpl
import cmath
mpl.use('pgf')

# Variables
data_rates = ['5Mbps', '2Mbps', '1Mbps', '500Kbps', '100Kbps']

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
    plt.savefig('{}.pgf'.format(filename))
    plt.savefig('{}.pdf'.format(filename))

# Read measurements
def read_measurements(input_file):
    # Setup variables
    throughput = {}

    # Open the input file
    with open(input_file, 'rb') as in_f:
        reader = csv.reader(in_f)

        # Go through all the measurements
        for row in reader:
            stas = int(row[1])
            if stas in throughput:
                throughput[stas]['cnt'] += 1
                throughput[stas]['tot'] += float(row[2])
                throughput[stas]['tot_avg'] = throughput[stas]['tot'] / throughput[stas]['cnt']
                throughput[stas]['sum'] += float(row[3])
                throughput[stas]['avg'] = throughput[stas]['sum'] / throughput[stas]['cnt']
                throughput[stas]['tot_sq'] += pow(float(row[2]), 2)
                throughput[stas]['var'] = (throughput[stas]['tot_sq'] - (pow(throughput[stas]['tot'], 2) / throughput[stas]['cnt'])) / throughput[stas]['cnt'];
                throughput[stas]['std'] = cmath.sqrt(throughput[stas]['var'])
            else:
                throughput[stas] = {}
                throughput[stas]['cnt'] = 1
                throughput[stas]['tot'] = float(row[2])
                throughput[stas]['tot_avg'] = float(row[2])
                throughput[stas]['sum'] = float(row[3])
                throughput[stas]['avg'] = float(row[3])
                throughput[stas]['tot_sq'] = pow(float(row[2]), 2)
                throughput[stas]['var'] = 0
                throughput[stas]['std'] = 0
            

    #Calculate total and mean
    throughput_tot = range(len(throughput))
    throughput_mean = range(len(throughput))
    throughput_err = range(len(throughput))
    stas_nb = range(len(throughput))
    for stas in throughput:
        stas_nb[stas-1] = stas
        throughput_tot[stas-1] = throughput[stas]['tot_avg']
        throughput_mean[stas-1] = throughput[stas]['avg']
        throughput_err[stas-1] = throughput[stas]['std']

    # Return information
    return (stas_nb, throughput_tot, throughput_mean, throughput_err)

# Plot throughput
def plot_throughput(stas, throughput_tot, throughput_mean, throughput_err, filename):
    # Generate the plot
    fig, ax = new_plot(0.9)
    ax.plot(stas, throughput_mean, 'b', label='Average throughput')
    ax.errorbar(stas, throughput_tot, yerr=throughput_err, fmt='r', label='Total throughput')
    ax.legend(loc='center right')
    ax.set_ylabel('Throughput MBps')
    ax.set_xlabel('STA count')
    save_plot(filename)

# Main function
if __name__ == '__main__':
    # Go through the datarates
    for dr in data_rates:
        (stas, throughput_tot, throughput_mean, throughput_err) = read_measurements("results/%s.csv" % dr)
        plot_throughput(stas, throughput_tot, throughput_mean, throughput_err, "results/%s" % dr)

