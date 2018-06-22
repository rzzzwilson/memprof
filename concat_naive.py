#!/usr/bin/env python3

"""
Test of "naive" string concatenation.
"""

import time
import common


a = ''

start = time.time()
for n in range(common.loops):
    a += str(n)

print(f'naive|{common.loops}|{time.time() - start}')
