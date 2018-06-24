#!/usr/bin/env python3

"""
Test of "comprehension" string concatenation.
"""

import sys
import time
import common
if sys.version_info >= (3, 0):
    # python3 - make changes
    xrange = range


start = time.time()
a = [str(n) for n in xrange(common.loops)]
a = ''.join(a)

print('comprehension|%d|%d' % (common.loops, time.time() - start))
