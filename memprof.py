#!/usr/bin/env python3

"""
"memprof" is a python program used to get a memory usage profile from
the execution of another python program.  "memprof" takes one or more
filenames and executes each file in another process, keeping track of
the memory used by the process.  Profile data is written to an output
file.

Usage: memprof [-h] [-i <file_list>] [-f <filename>] [-o <profile_file>]

where -h                  prints help messages and quits,
      -i <name_file>      profiles name+filename (cumulative),
      -f <filename>       read <filename> for a list of names+files to profile,
      -g <plotimage>      if specified, the path to the plot file to produce
      -o <profile_file>   write profile data to <profile_file>
                          (default "profile.out").
      -s <outdir>         sets the directory to receive stdout capture files
                          (default "stdout")
      -p <2|3>            use python 2 or 3 to execute filenames (3 is default)
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


# default output filename and stdout save dir
DefaultOutputFile = 'memprof.out'
DefaultStdoutSave = 'stdout'

# versions of python to use
DefaultPython2 = 'python'
DefaultPython3 = 'python3'


def abort(msg):
    """Print some meaningful message and then quit the program."""

    print(f"\n{'*'*60}\n{msg}\n{'*'*60}\n")
    sys.exit(1)

def get_platform_info(python_exe):
    """Get a string describing the execution platform.
    
    python_exe  path to the python used to execute external programs 

    Returns a string like: 
    """

    return subprocess.check_output(f'{python_exe} python_info.py',
                                   stderr=subprocess.STDOUT, shell=True).decode("utf-8").strip()

def canon_name_file(param):
    """Convert name+filename to canonical form.

    param  a string of form "path_to_exe" or "name,path_to_exe".

    Return a tuple (name, path_to_exe) where "name" is the basename of
    the path if not supplied.

    Returns None if something went wrong.
    """

    name_file = param.split(',')
    if len(name_file) == 1:
        name = os.path.basename(param)
        filename = param
    elif len(name_file) == 2:
        (name, filename) = name_file
    else:
        return None

    return (name, filename)

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

    lines = [f.strip() for f in lines if f.strip()]
    lines = [line for line in lines if not line.startswith('#')]

    result = []

    for line in lines:
        canon = canon_name_file(line)
        if canon is None:
            abort(f"Bad line in file '{path}': {line}")
        result.append(canon)

    return result

def memprof(files, output_file, save_dir, python_exe):
    """Create a memory profile of one or more executable files.

    files        a list of names+executable files
    output_file  the file to write profile information to
    save_dir     the directory in which to store stdout save files
    python_exe   the python to execute the executable files with
    """

    # create the save directory, if necessary
    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)

    # open the stats save file
    fd = open(output_file, 'w')

    # process each executable
    for (name, exe_path) in files:
        stdout_save = os.path.join(save_dir, name + '.stdout')
        if not os.path.isabs(exe_path):
            exe_path = os.path.abspath(exe_path)

        command = '%s %s' % (python_exe, exe_path)
        with open(stdout_save, 'w') as save_fd:
            process = subprocess.Popen(command, shell=True, stdout=save_fd)
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
        (opts, args) = getopt.getopt(argv, 'hg:i:f:o:p:s:',
                                     ['help', 'graph=', 'input=', 'file=',
                                      'output=', 'python=', 'save='])
    except getopt.GetoptError as err:
        usage(err)
        sys.exit(1)
    
    output_file = DefaultOutputFile
    save_dir = DefaultStdoutSave
    python_exe = DefaultPython3
    plot_file = None
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
            file_list = read_input_file(param)
        if opt in ['-o', '--output']:
            output_file = param
        if opt in ['-p', '--python']:
            if param not in ['2', '3']:
                abort()
            if param == '2':
                python_exe = DefaultPython2
            if param == '3':
                python_exe = DefaultPython3
        if opt in ['-s', '--save']:
            if param == '2':
                python_exe = DefaultPython2
        if opt in ['-s', '--save']:
            if param == '2':
                python_exe = DefaultPython2
        if opt in ['-s', '--save']:
            save_dir = param

    # sanity check
    if not file_list:
        usage()
        abort('You must supply one or more executable files to profile.')
    
    # run the program code
    memprof(file_list, output_file, save_dir, python_exe)

    # if plot needed, do it
    if plot_file:
        p_info = get_platform_info(python_exe)
        plot.plot(output_file, plot_file, p_info)

main()
