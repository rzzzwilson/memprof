Overview
========

*memprof* is a python program used to get a memory usage profile from
the execution of another executable program.  *memprof* takes one or more
names+filenames and executes each file in another process, keeping track of
the memory used by the process.  Profile data is written to an output
file.

See the *__doc__* string in memprof.py for usage.

This program was written to help determine memory usage in various of the
performance tests elsewhere in this GitHub repository.

Requirements
------------

Uses the *psutil* module, which you can get from: https://pypi.org/project/psutil/
Alternatively, do::

    pip3 install -r requirements.txt
