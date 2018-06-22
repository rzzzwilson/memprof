#!/usr/bin/env python3

"""
Test of "join" string concatenation.
"""

import time
import common


a = []
start = time.time()

for n in range(common.loops):
    a.append(str(n))
a = ''.join(a)

print(f'join|{common.loops}|{time.time() - start}')
