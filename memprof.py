#!/usr/bin/env python3

"""
"memprof" is a program used to get a memory usage profile from the execution of
one or more external programs.  A plot file is produced showing memory usage of
each program with time.  The raw plot data may optionally be saved to a file.

Usage: memprof [-a <annotation>] [-h] [-i <file_list>] [-f <filename>]   \\
               [-o <profile_file>] [-p <plotimage>] [-q]                 \\
               [-s <stdout_save_dir>] [-x <data_file>]

where -a <annotation>       put the string <annotation> into the plot file
      -h                    prints help messages and quits,
      -i <name_file>        profiles name+filename (cumulative),
      -f <filename>         get list of name+filename from file (cumulative),
      -o <profile_file>     optionally write raw profile data to <profile_file>
      -p <plotimage>        if specified, the path to the plot file to produce
                            (default "memprof.png")
      -q                    don't show the plot file, just save it
      -s <stdout_save_dir>  path to the directory to save "stdout" files
      -x <data_file>        just plot data from <data_file>
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
DefaultOutputPlot = 'memprof.png'
DefaultStdoutSaveDir = '__stdout__'

# plot memory size multiplier/divisors
KiloByte = 1024
MegaByte = 1024*1024
GigaByte = 1024*1024*1024


def plot_graph(t, m, anno, plot_file, quiet, p_info, dt, annotation):
    """
    Plot a graph.

    t           time series
    m           memory series
    anno        a list of tuples - annotations
    quiet       True if we *don't* display graph on screen
    p_info      platform description string
    dt          datetime string of data last modification
    annotation  annotation string, if one
    """

    # get max values of memory and time series
    max_m = max(m)
    max_t = max(t)
    basetime = t[0]

    # figure out the best unit to plot with: B, KB or MB
    divisor = GigaByte
    unit = 'GB'

    if max_m < GigaByte:
        divisor = MegaByte
        unit = 'MB'
    if max_m < MegaByte:
        divisor = KiloByte
        unit = 'KB'
    if max_m < KiloByte:
        divisor = 1
        unit = 'B'

    # scale the data, get maximum values
    m = [x/divisor for x in m]
    max_m = max(m)

    # figure out where to place the test name
    test_anno_y = max(m)
    if max_m < 10:
        test_anno_y = max(m)
    elif max_m < 100:
        test_anno_y = (max(m) // 10) * 10
    elif max_m < 1000:
        test_anno_y = (max(m) // 100) * 100
    elif max_m < 10000:
        test_anno_y = (max(m) // 1000) * 1000

    # start the plot
    (fig, ax) = plt.subplots()

    # plot actual data, set labels and turn on grod
    ax.plot(t, m)
    ax.set(xlabel='time (s)', ylabel=f'Memory used ({unit})',
           title='Memory usage by time')
    ax.grid()

    # draw a rectangel around each series, draw series annotation
    # anno tuple is: (name, max_mem, start_time, stop_time)
    matplotlib.rc('font', **{'size': 7})  # set font size smaller
    for (i, (name, max_mem, start_t, end_t)) in enumerate(anno):
        # put the rectange around the series data
        rect = patches.Rectangle((start_t-basetime, -1000), end_t-start_t, 2*max_m+1000,
                                 linewidth=1, edgecolor='red', facecolor='#f0f0f080')
        ax.add_patch(rect)

        # add annotation
        label = f'{name} - {end_t-start_t:.2f}s, {max_mem/divisor:.2f}{unit} max'
        ax.text(start_t, test_anno_y, label,
                rotation=270, horizontalalignment='left', verticalalignment='top')

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
    ax.annotate(f'generated on {dt}', xy=(0, 0),
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
    plot_file    path to the output plot image file
    annotation   the annotation string (None if none)
    quiet        True if we *don't* display the graph on the screen
    """

    # data file contains lines of this format:
    #     1529579605.214047|name|274432
    # but the first line is a comment containing platform info and
    # the date the data was generated:
    #     # Darwin-17.6.0-x86_64-i386-64bit|2018-07-02T07:28:11Z

    # get all lines within the data file
    with open(input_file) as fd:
        lines = fd.readlines()

    # first line contains a platform description and data generation time
    tmp = lines[0].strip()
    lines = lines[1:]

    p_info = None
    datetime_zulu = None

    if tmp.startswith('#'):
        (p_info, datetime_zulu) = tmp[1:].split('|')
    else:
        raise RuntimeError(f"Line 0 of file {input_file} missing annotation, got '{tmp}'")

    # split data into two parallel lists of lists of mem size and timestamp,
    # one for each test in the file.
    data_time = []
    data_mem = []
    anno = []
    start_time = float(lines[0].split('|')[0])    # first line start time
    last_name = None
    max_mem = 0     # max memory used for a test

    # temporary collectors of time/mem data for one test
    # these are appended to data_time/data_mem when tets name changes
    time_series = []
    mem_series = []

    for line in lines:
        if not line.strip():
            continue        # skip blank lines (at end of file?)
        (time_val, name, mem_val) = line.split('|')
        time_val = float(time_val)
        time_val -= start_time
        mem_val = int(mem_val)

        if last_name != name:
            if last_name is not None:
                data_time.append(time_series)
                data_mem.append(mem_series)
                anno.append((last_name, max_mem, time_series[0], time_series[-1]))
            
            time_series = []
            mem_series = []
            last_name = name
            max_mem = 0

        time_series.append(time_val)
        mem_series.append(mem_val)

        if mem_val > max_mem:
            max_mem = mem_val

    data_time.append(time_series)
    data_mem.append(mem_series)
    anno.append((name, max_mem, time_series[0], time_series[-1]))

    # now, join the individual test series data together with a 0 for memory
    # at each start/end of a test series, using start/end time
    new_data_time = []
    new_data_mem = []
    for (t, m) in zip(data_time, data_mem):
        new_data_time.append(t[0])
        new_data_time.extend(t)
        new_data_time.append(t[-1])

        new_data_mem.append(0)
        new_data_mem.extend(m)
        new_data_mem.append(0)

    plot_graph(new_data_time, new_data_mem, anno,
               plot_file, quiet, p_info, datetime_zulu, annotation)


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

    # open the stats save file and write platform string and timestamp
    fd = open(output_file, 'w')
    p_info = get_platform_info()

    gt = time.gmtime()
    datetime_zulu = time.strftime('%Y-%m-%dT%H:%M:%SZ', gt)

    fd.write(f'# {p_info}|{datetime_zulu}\n')

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
    """Print the module docstring and optional msg."""

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
        (opts, args) = getopt.getopt(argv, 'a:hi:f:o:p:qs:x:',
                                     ['annotation=', 'help', 'input=', 'file=',
                                      'output=', 'plot=', 'quiet',
                                      'save=', 'xdebug='])
    except getopt.GetoptError as err:
        usage(err)
        sys.exit(1)
   
    annotation = None               # default is no annotation
    data_file = None                # default is no saved raw data file
    save_output = False             # don't save raw data is default
    plot_file = DefaultOutputPlot
    quiet = False
    save_stdout = False
    save_dir = DefaultStdoutSaveDir
    prog_list = []
    x_file = None
    
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
            save_output = True
            data_file = param
        elif opt in ['-p', '--plot']:
            plot_file = param
        elif opt in ['-q', '--quiet']:
            quiet = True
        elif opt in ['-s', '--save']:
            save_stdout = True
            save_dir = param
        elif opt in ['-x', '--xdebug']:
            x_file = param

    # sanity check
    if not prog_list:
        usage()
        abort('You must supply one or more executable files to profile.')
    
    # if no data save file, create a temporary file for raw data
    if not save_output:
        (_, data_file) = tempfile.mkstemp(suffix='.tmp', prefix='memprof_',text=True)

    # if no stdout save directory, create a temporary directory for files
    if not save_stdout:
        save_dir = tempfile.mkdtemp(suffix='.tmp', prefix='memprof_')

    # run the sampling to get the raw data, and plot
    if not x_file:
        memprof(prog_list, data_file, save_dir)
        plot(data_file, plot_file, annotation, quiet)
    else:
        # but just plot existing data file for debug
        plot(x_file, plot_file, annotation, quiet)

    # if not saving raw data file, delete data
    if not save_output:
        os.remove(data_file)

    # if not saving stdout output, delete whole directory
    if not save_stdout:
        shutil.rmtree(save_dir, ignore_errors=True)


main()
