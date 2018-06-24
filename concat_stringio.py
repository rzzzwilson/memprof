#!/usr/bin/env python3

"""
Test of "stringIO" string concatenation.
"""

import time
import common
try:
    from cStringIO import StringIO
except ImportError:
    # python3 - make changes
    import io
    global StringIO
    StringIO = io.StringIO
    xrange = range


a = StringIO()
start = time.time()
for n in xrange(common.loops):
    a.write(str(n))
a = a.getvalue()

print('stringIO|%d|%f' % (common.loops, time.time() - start))

