#!/usr/bin/env python3

"""
Plot and save a memprof dataset.

Usage:  plot.py [-h] [-m] [-o <output_image>] [-q] <input_file>

where -h                 prints help text and stops
      -m                 use MiB memory size, not MB
      -o <output_image>  saves the image in file <output_image>
      -q                 be "quiet" - don't show graph, just save
      <input_file>       the memprof data file to plot
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import common


# memory size multiplier and title
Mebibyte = (1000000, 'MiB')
Megabyte = (1024*1024, 'MB')

# default output file
DefaultOutputFile = 'test.png'


def plot_graph(t, s, anno, unit_name, output_file, quiet, p_info):
    """
    Plot a graph.

    t          time series
    s          data series
    anno       a list of tuples - annotations
    unit_name  string holding units
    quiet      True if we *don't* display graph on screen
    p_info     optional platform description string
    """

    max_t = max(t)
    max_s = (max(s) // 100) * 100

    (fig, ax) = plt.subplots()
    ax.plot(t, s)
    ax.set(xlabel='time (s)', ylabel=f'Memory used ({unit_name})',
           title=f'Memory usage by time')
    ax.grid()

    # draw a rectangle around the sub-graph for each name, alternate colors
    matplotlib.rc('font', **{'size': 8})  # set font size smaller
    for (i, (end_time, delta, name, max_mem)) in enumerate(anno):
        color = '#F0F0F080' if (i % 2) == 0 else '#FFFFFF00'
        rect = patches.Rectangle((end_time-delta,-100), delta, 2*max_s,
                                 linewidth=1, ec='red', fc=color)
        ax.add_patch(rect)

        ax.text(end_time-delta, max_s, f' {name} - {delta:.2f}s, {max_mem:.2f} {unit_name}',
                rotation=270, horizontalalignment='left', verticalalignment='top')

    # put the number of loops in as a "footnote"
    matplotlib.rc('font', **{'size': 6})  # set font size smaller
    ax.annotate(f'{common.loops:,} concatenations', xy=(0, 0), 
                xycoords='data', rotation=270,
                xytext=(1.003, 0.00), textcoords='axes fraction',
                horizontalalignment='left', verticalalignment='bottom')

    # put the platform description string in if we have one
    if p_info:
        matplotlib.rc('font', **{'size': 6})  # set font size smaller
        ax.annotate(f'{p_info}', xy=(0, 0),
                    xycoords='data', rotation=270,
                    xytext=(1.003, 1.00), textcoords='axes fraction',
                    horizontalalignment='left', verticalalignment='top')

    # save graph and show, if required
    fig.savefig(output_file, dpi=1000)
    if not quiet:
        plt.show()


def plot(input_file, output_file, p_info=None, quiet=False, unit=Megabyte):
    """Analyze then draw a plot image file.

    input_file   path to the memprof data file to analyze
    output_file  path to the output plot image file
    p_info       optinal string describing platform
    unit         a tuple of (multiplier, name)
    quiet        True if we *don't* display the graph on the screen

    """

    # break out the unit name and multiplier
    (unit_mult, unit_name) = unit

    # read data from file
    # format: 1529579605.214047|name|274432
    #         time              name memory
    with open(input_file) as fd:
        lines = fd.readlines()

    t = []
    s = []
    anno = []
    start_time = None
    last_name = None
    last_start = None
    max_mem = 0     # max memory used for a test

    for line in lines:
        (t_elt, name, s_elt) = line.split('|')
        t_elt = float(t_elt)

        if start_time is None:
            start_time = t_elt

        t_elt -= start_time
        s_elt = int(s_elt)/unit_mult

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

    plot_graph(t, s, anno, unit_name, output_file, quiet, p_info)

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
            (opts, args) = getopt.getopt(argv, 'hmo:q',
                                         ['help', 'mib', 'output=', 'quiet'])
        except getopt.GetoptError as err:
            usage(err)
            sys.exit(1)

        output_file = DefaultOutputFile
        unit = Megabyte
        p_info = None       # not used if run on commandline
        quiet = False

        for (opt, param) in opts:
            if opt in ['-h', '--help']:
                usage()
                sys.exit(0)
            if opt in ['-m', '--mib']:
                unit = Mebibyte
            if opt in ['-o', '--output']:
                output_file = param
            if opt in ['-q', '--quiet']:
                quiet = True

        # we MUST have a single input filename
        if len(args) != 1:
            usage('You must supply a memprof data file to plot')
            sys.exit(1)

        # run the program code
        plot(args[0], output_file, p_info, quiet, unit)


    main()

