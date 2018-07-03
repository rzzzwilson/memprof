#!/usr/bin/env python3

"""
Test of "join" string concatenation.
"""

import sys
if sys.version_info >= (3, 0):
    # python3 - make changes
    xrange = range


a = []
for n in xrange(20000000):
    a.append(str(n))
a = ''.join(a)
