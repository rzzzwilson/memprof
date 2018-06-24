#!/usr/bin/env python3

"""
Test of "stringIO" string concatenation.
"""

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
for n in xrange(common.loops):
    a.write(str(n))
a = a.getvalue()
