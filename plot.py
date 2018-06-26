#!/usr/bin/env python3

"""
Plot and save a memprof dataset.

Usage:  plot.py [-h] [-m] [-o <output_image>] [-q] <input_file>

where -h                 prints help text and stops
      -o <output_image>  saves the image in file <output_image>
      -q                 be "quiet" - don't show graph, just save
      <input_file>       the memprof data file to plot
"""

import time
import os.path
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.lines as mlines
import common


# memory size multiplier/divisors
KiloByte = 1024
MegaByte = 1024*1024
GigaByte = 1024*1024*1024

# default output file
DefaultOutputFile = 'test.png'


def get_platform_info():
    """Get a string describing the execution platform."""

    return platform.platform().strip()


def plot_graph(t, s, p_info, anno, output_file, quiet, dt):
    """
    Plot a graph.

    t       time series
    s       data series
    p_info  platform description string
    anno    a list of tuples - annotations
    quiet   True if we *don't* display graph on screen
    dt      datetime string of data last modification
    """

    # get max values of memory and time series
    max_s = max(s)
    max_t = max(t)
    basetime = t[0]

    # figure out the best unit to plot with: B, KB or MB
    divisor = GigaByte
    unit = 'GB'

    if max_s < GigaByte:
        divisor = MegaByte
        unit = 'MB'
    if max_s < MegaByte:
        divisor = KiloByte
        unit = 'KB'
    if max_s < KiloByte:
        divisor = 1
        unit = 'B'

    # scale the data
    s = [x/divisor for x in s]
    max_s = max(s)

    # figure out where to place the test name
    test_anno_y = max(s)
    if max_s < 10:
        test_anno_y = max(s)
    elif max_s < 100:
        test_anno_y = (max(s) // 10) * 10
    elif max_s < 1000:
        test_anno_y = (max(s) // 100) * 100
    elif max_s < 10000:
        test_anno_y = (max(s) // 1000) * 1000

    # start the plot
    (fig, ax) = plt.subplots()

    ax.plot(t, s)
    ax.set(xlabel='time (s)', ylabel=f'Memory used ({unit})',
           title=f'Memory usage by time')
    ax.grid()

    # draw a line at the start of each series, draw series annotation
    matplotlib.rc('font', **{'size': 7})  # set font size smaller
    for (i, (end_time, delta, name, max_mem)) in enumerate(anno):
        l = mlines.Line2D([end_time-delta,end_time-delta], [-1000,2*max_s],
                          linewidth=1, color='red')
        ax.add_line(l)

        ax.text(end_time-delta, test_anno_y,
                f'{name} - {delta:.2f}s, {max_mem/divisor:.2f}{unit} max',
                rotation=270, horizontalalignment='left', verticalalignment='top')

    # put in final line - end of last test
    l = mlines.Line2D([max_t-basetime,max_t-basetime], [-1000,2*max_s],
                          linewidth=1, color='red')
    ax.add_line(l)

    # put the number of loops in as a "footnote"
    matplotlib.rc('font', **{'size': 5})  # set font size smaller
    ax.annotate(f'{common.loops:,} concatenations', xy=(0, 0), 
                xycoords='data', rotation=270,
                xytext=(1.003, 0.00), textcoords='axes fraction',
                horizontalalignment='left', verticalalignment='bottom')

    # put the platform description string in if we have one
    if p_info:
        matplotlib.rc('font', **{'size': 5})  # set font size smaller
        ax.annotate(f'{p_info}', xy=(0, 0),
                    xycoords='data', rotation=270,
                    xytext=(1.003, 1.00), textcoords='axes fraction',
                    horizontalalignment='left', verticalalignment='top')

    # put a 'date/time modified' string on the graph
    matplotlib.rc('font', **{'size': 4})  # set font size smaller
    ax.annotate(f'from data generated on {dt}', xy=(0, 0),
                xycoords='data', #rotation=270,
                xytext=(1.0, -0.095), textcoords='axes fraction',
                horizontalalignment='right', verticalalignment='top')

    # save graph and show, if required
    fig.savefig(output_file, dpi=1000)
    if not quiet:
        plt.show()


def plot(input_file, output_file, quiet=False):
    """Analyze then draw a plot image file.

    input_file   path to the memprof data file to analyze
    output_file  path to the output plot image file
    quiet        True if we *don't* display the graph on the screen

    """

    # get date/time of last data modification
    data_time = os.path.getmtime(input_file)
    gm_struct = time.gmtime(data_time)
    datetime_zulu = time.strftime('%Y-%m-%dT%H:%M:%SZ', gm_struct)

    # read data from file
    # format: 1529579605.214047|name|274432
    #         time              name memory
    with open(input_file) as fd:
        lines = fd.readlines()

    # first line should be a comment containing a platform description
    tmp = lines[0].strip()
    p_info = None
    if tmp.startswith('#'):
        tmp = tmp[1:]
        while tmp[0] == ' ':
            tmp = tmp[1:]
        p_info = tmp
        lines = lines[1:]

    # get the actual data into memory
    t = []
    s = []
    anno = []
    start_time = None
    last_name = None
    last_start = None
    max_mem = 0     # max memory used for a test

    for line in lines:
        if not line.strip():
            continue        # skip blank lines (at end of file?)
        (t_elt, name, s_elt) = line.split('|')
        t_elt = float(t_elt)

        if start_time is None:
            start_time = t_elt

        t_elt -= start_time
        s_elt = int(s_elt)

        s.append(s_elt)
        t.append(t_elt)

        if last_name != name:
            if last_name:
                delta = t_elt - last_start
                anno.append((t_elt, delta, last_name, max_mem))
            last_name = name
            last_start = t_elt
            max_mem = 0

        if s_elt > max_mem:
            max_mem = s_elt

    delta = t_elt - last_start
    anno.append((t_elt, delta, last_name, max_mem))

    plot_graph(t, s, p_info, anno, output_file, quiet, datetime_zulu)


if __name__ == '__main__':
    import sys
    import getopt

    def usage(msg=None):
        """Display some help on the console.

        msg  informative message to display

        Also prints the module doc string.
        """

        if msg:
            print(('*'*80 + '\n%s\n' + '*'*80) % msg)
        print(__doc__)


    def main():
        """Parse all params and call the analyze/plot code."""

        # parse the CLI params
        argv = sys.argv[1:]

        try:
            (opts, args) = getopt.getopt(argv, 'ho:q',
                                         ['help', 'output=', 'quiet'])
        except getopt.GetoptError as err:
            usage(err)
            sys.exit(1)

        output_file = DefaultOutputFile
        p_info = None       # not used if run on commandline
        quiet = False

        for (opt, param) in opts:
            if opt in ['-h', '--help']:
                usage()
                sys.exit(0)
            if opt in ['-o', '--output']:
                output_file = param
            if opt in ['-q', '--quiet']:
                quiet = True

        # we MUST have a single input filename
        if len(args) != 1:
            usage('You must supply a memprof data file to plot')
            sys.exit(1)

        # run the program code
        plot(args[0], output_file, quiet)


    main()

