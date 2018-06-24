#!/usr/bin/env python3

"""
Test of "join" string concatenation.
"""

import sys
import time
import common
if sys.version_info >= (3, 0):
    # python3 - make changes
    xrange = range


a = []
start = time.time()

for n in xrange(common.loops):
    a.append(str(n))
a = ''.join(a)

print('join|%d|%d' % (common.loops, time.time() - start))
