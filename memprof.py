#!/usr/bin/env python3

"""
"memprof" is a python program used to get a memory usage profile from
the execution of another python program.  "memprof" takes one or more
filenames and executes each file in another process, keeping track of
the memory used by the process.  Profile data is written to an output
file.

Usage: memprof [-g <plotimage>] [-h] [-i <file_list>] [-f <filename>] \\
               [-o <profile_file>] [-s <stdout_save_dir>

where -g <plotimage>        if specified, the path to the plot file to produce
                            (default "memprof.png")
      -h                    prints help messages and quits,
      -i <name_file>        profiles name+filename (cumulative),
      -f <filename>         get list of name+filename from file (cumulative),
      -o <profile_file>     write profile data to <profile_file>
                            (default "memprof.out").
      -s <stdout_save_dir>  path to the directory to save "stdout" files
"""

import os
import sys
import time
import getopt
import platform
import traceback
import subprocess
import psutil
import plot


# default output filenames
DefaultOutputFile = 'memprof.out'
DefaultOutputPlot = 'memprof.png'
DefaultStdoutSaveDir = '__stdout__'


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
        print(('*'*80 + '\n%s\n' + '*'*80) % msg)

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
        (opts, args) = getopt.getopt(argv, 'hg:i:f:o:s:',
                                     ['help', 'graph=', 'input=',
                                      'file=', 'output=', 'save='])
    except getopt.GetoptError as err:
        usage(err)
        sys.exit(1)
    
    output_file = DefaultOutputFile
    plot_file = DefaultOutputPlot
    save_dir = DefaultStdoutSaveDir
    file_list = []
    
    for (opt, param) in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)
        if opt in ['-g', '--graph']:
            plot_file = param
        if opt in ['-i', '--input']:
            # 'param' is either "filename" or "name,filename"
            result = canon_name_file(param)
            if result is None:
                abort(f"'-i' option must be 'filename' or 'name,filename'")
            file_list.append(result)
        if opt in ['-f', '--file']:
            file_list.extend(read_input_file(param))
        if opt in ['-o', '--output']:
            output_file = param
        if opt in ['-s', '--save']:
            save_dir = param

    # sanity check
    if not file_list:
        usage()
        abort('You must supply one or more executable files to profile.')
    
    # run the program code
    memprof(file_list, output_file, save_dir)

    # if plot needed, do it
    if plot_file:
        plot.plot(output_file, plot_file)

main()
