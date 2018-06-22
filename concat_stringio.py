#!/usr/bin/env python3

"""
Test of "stringIO" string concatenation.
"""

import time
import common
from io import StringIO


a = StringIO()
start = time.time()
for n in range(common.loops):
    a.write(str(n))
a = a.getvalue()

print(f'stringIO|{common.loops}|{time.time() - start}')

