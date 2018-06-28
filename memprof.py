#!/usr/bin/env python3

"""
"memprof" is a program used to get a memory usage profile from the execution of
one or more external programs.  A plot file is produced showing memory usage of
each program with time.  The raw plot data may optionally be saved to a file.

Usage: memprof [-h] [-i <file_list>] [-f <filename>] [-o <profile_file>]  \\
                   [-p <plotimage>] [-q] [-s <stdout_save_dir>]

where -a <annotation>       put the string <annotation> into the plot file
      -h                    prints help messages and quits,
      -i <name_file>        profiles name+filename (cumulative),
      -f <filename>         get list of name+filename from file (cumulative),
      -o <profile_file>     optionally write raw profile data to <profile_file>
      -p <plotimage>        if specified, the path to the plot file to produce
                            (default "memprof.png")
      -q                    don't show the plot file, just save it
      -s <stdout_save_dir>  path to the directory to save "stdout" files
                            (default "__stdout__")
"""

import os
import sys
import time
import shutil
import getopt
import tempfile
import platform
import traceback
import subprocess

import psutil
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.lines as mlines


# default output filenames
#DefaultOutputFile = 'memprof.out'
DefaultOutputPlot = 'memprof.png'
DefaultStdoutSaveDir = '__stdout__'

# plot memory size multiplier/divisors
KiloByte = 1024
MegaByte = 1024*1024
GigaByte = 1024*1024*1024


def plot_graph(t, s, p_info, anno, plot_file, quiet, dt, annotation):
    """
    Plot a graph.

    t           time series
    s           data series
    p_info      platform description string
    anno        a list of tuples - annotations
    quiet       True if we *don't* display graph on screen
    dt          datetime string of data last modification
    annotation  annotation string, if one
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
    ax.set(xlabel='time (s)', ylabel='Memory used ({unit}s)',
           title='Memory usage by time')
    ax.grid()

    # draw a line at the start of each series, draw series annotation
    matplotlib.rc('font', **{'size': 7})  # set font size smaller
    for (i, (end_time, delta, name, max_mem)) in enumerate(anno):
        l = mlines.Line2D([end_time-delta,end_time-delta], [-1000,2*max_s],
                          linewidth=1, color='red')
        ax.add_line(l)

        label = f'{name} - {delta:.2f}s, {max_mem/divisor:.2f}{unit} max'
        ax.text(end_time-delta, test_anno_y, label,
                rotation=270, horizontalalignment='left', verticalalignment='top')

    # put in final line - end of last test
    l = mlines.Line2D([max_t-basetime,max_t-basetime], [-1000,2*max_s],
                          linewidth=1, color='red')
    ax.add_line(l)

    # put the test annotation in as a "footnote"
    if annotation:
        matplotlib.rc('font', **{'size': 5})  # set font size smaller
        ax.annotate(annotation, xy=(0, 0), 
                    xycoords='data', rotation=270,
                    xytext=(1.003, 0.00), textcoords='axes fraction',
                    horizontalalignment='left', verticalalignment='bottom')

    # put the platform description string in if we have one
    if p_info:
        matplotlib.rc('font', **{'size': 5})  # set font size smaller
        ax.annotate(p_info, xy=(0, 0),
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
    fig.savefig(plot_file, dpi=1000)
    if not quiet:
        plt.show()


def plot(input_file, plot_file, annotation=None, quiet=False):
    """Analyze then draw a plot image file.

    input_file   path to the memprof data file to analyze
    plot_file  path to the output plot image file
    annotation   the annotation string (None if none)
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

    plot_graph(t, s, p_info, anno, plot_file, quiet, datetime_zulu, annotation)


def get_platform_info():
    """Get a string describing the execution platform."""

    return platform.platform().strip()


def abort(msg):
    """Print some meaningful message and then quit the program."""

    print(f"\n{'*'*60}\n{msg}\n{'*'*60}\n")
    sys.exit(1)


def canon_name_file(param):
    """Convert name+filename to canonical form.

    param  a string of form "name,path_to_exe".

    Return a tuple (name, path_to_exe).

    Returns None if something went wrong.
    """

    name_file = param.split(',')
    if len(name_file) == 2:
        return name_file

    return None


def read_input_file(path):
    """Read input file and return list of filenames.

    path  path to file containing names and filenames, one per line

    Returns a list of names and filenames from the file.
    Blank lines and lines that start with '#' are ignored.
    """

    try:
        with open(path, 'r') as fd:
            lines = fd.readlines()
    except FileNotFoundError as e:
        abort(f"File '{path}' not found")


    result = []

    for (lnum, line) in enumerate(lines):
        s_line = line.strip()
        if s_line.startswith('#'):
            continue
        canon = canon_name_file(s_line)
        if canon is None:
            abort(f"Bad line {lnum+1} in file '{path}': {line}")
        result.append(canon)

    return result


def memprof(files, output_file, save_dir):
    """Create a memory profile of one or more executable files.

    files        a list of names+executable files
    output_file  the file to write profile information to
    save_dir     the path to the directory to save stdout in
    """

    # open the stats save file and write platform string
    fd = open(output_file, 'w')
    p_info = get_platform_info()
    fd.write(f'# {p_info}\n')

    # create the output save directory
    try:
        os.mkdir(save_dir)
    except FileExistsError:
        pass        # already exists

    # process each executable
    for (name, command) in files:
        # open the stdout save file
        std_file = os.path.join(save_dir, f'{name}.stdout')
        with open(std_file, 'a') as std_save:
            process = subprocess.Popen(command, shell=True,
                                       stdout=std_save, stderr=std_save)
            pid = process.pid

            # now do memory profile until process quits
            try:
                ps_proc = psutil.Process(pid)
                while process.poll() == None:
                    fd.write(f'{time.time():.6f}|{name}|{ps_proc.memory_info().rss}\n')
                time.sleep(0.005)
            except (ProcessLookupError, psutil._exceptions.AccessDenied):
                # we get either of the above two exceptions sometimes
                pass

    fd.close()


# to help the befuddled user
def usage(msg=None):
    print(__doc__)
    if msg:
        delim = '*'*80
        print(f'{delim}\n{msg}\n{delim}\n')

# our own handler for uncaught exceptions
def excepthook(type, value, tb):
    msg = '\n' + '=' * 80
    msg += '\nUncaught exception:\n'
    msg += ''.join(traceback.format_exception(type, value, tb))
    msg += '=' * 80 + '\n'
    print(msg)

def main():
    # plug our handler into the python system
    sys.excepthook = excepthook
    
    # parse the CLI params
    argv = sys.argv[1:]
   
    try:
        (opts, args) = getopt.getopt(argv, 'a:hi:f:o:p:qs:',
                                     ['annotation=', 'help', 'input=', 'file=',
                                      'output=', 'plot=', 'quiet', 'save='])
    except getopt.GetoptError as err:
        usage(err)
        sys.exit(1)
   
    # create a temporary file for raw data
    (_, data_file) = tempfile.mkstemp(suffix='.tmp', prefix='memprof_',text=True)

    annotation = None               # default is no annotation
    output_file = None              # default is no saved raw data file
    plot_file = DefaultOutputPlot
    quiet = False
    save_dir = DefaultStdoutSaveDir
    prog_list = []
    
    for (opt, param) in opts:
        if opt in ['-a', '--annotation']:
            annotation = param
        elif opt in ['-h', '--help']:
            usage()
            sys.exit(0)
        elif opt in ['-i', '--input']:
            result = canon_name_file(param)
            if result is None:
                abort("'-i' option must be 'name,filename'")
            prog_list.append(result)
        elif opt in ['-f', '--file']:
            prog_list.extend(read_input_file(param))
        elif opt in ['-o', '--output']:
            output_file = param
        elif opt in ['-p', '--plot']:
            plot_file = param
        elif opt in ['-q', '--quiet']:
            quiet = True
        elif opt in ['-s', '--save']:
            save_dir = param

    # sanity check
    if not prog_list:
        usage()
        abort('You must supply one or more executable files to profile.')
    
    # run the sampling to get the raw data
    memprof(prog_list, data_file, save_dir)

    # plot the raw data
    plot(data_file, plot_file, annotation, quiet)

    # if raw data file required to be saved, copy tmp file to save file
    if output_file:
        shutil.copyfile(data_file, output_file)

    # delete the temporary file
    os.remove(data_file)


main()
