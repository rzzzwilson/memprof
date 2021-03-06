Overview
========

*memprof* is a program used to get a memory usage profile from the execution of
one or more external programs.  A plot file is produced showing memory usage of
each program with time.  The raw plot data may optionally be saved to a file.

*memprof* is a python3.6+ program only, but the monitored programs may be any
type of executable.

Usage
-----

::

    memprof [-a <annotation>] [-h] [-i <file_list>] [-f <filename>]   \
            [-o <profile_file>] [-p <plotimage>] [-q]                 \
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

Examples
--------

To run a series of tests, you can put test information in a file.  Here is the
contents of the `test_files.dat` file::

    naive - python3,python3 examples/concat_naive.py
    join - python3,python3 examples/concat_join.py
    comprehension - python3,python3 examples/concat_comprehension.py
    stringio - python3,python3 examples/concat_stringio.py

The data format is similar the that required for the `-i` option.  When we run
these four tests with `memprof`::

    ./memprof.py -p test.png -f test_files.dat -o test.out -a "20,000,000 iterations"

we get the output image:

.. image:: example.png

We can run any command.  Doing this at the command line::

    ./memprof.py -i test,"ls -lR" -i test2,"ls -lR" -a "test annotation" -q -p example.png

results in this plot file:

.. image:: example2.png

Requirements
------------

Uses the *psutil* module, which you can get from: https://pypi.org/project/psutil/ .

Also uses *matplotlib* to plot the graph, get from: https://matplotlib.org/faq/installing_faq.html .

Alternatively, do::

    pip3 install -r requirements.txt
