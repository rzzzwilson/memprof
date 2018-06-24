#!/usr/bin/env python3

"""
Test of "naive" string concatenation.
"""

import sys
import time
import common
if sys.version_info >= (3, 0):
    # python3 - make changes
    xrange = range


a = ''

start = time.time()
for n in xrange(common.loops):
    a += str(n)

print('naive|%d|%d' % (common.loops, time.time() - start))
