#!/usr/bin/env python3

"""
Test of "join" string concatenation.
"""

import sys
import common
if sys.version_info >= (3, 0):
    # python3 - make changes
    xrange = range


a = []
for n in xrange(common.loops):
    a.append(str(n))
a = ''.join(a)
