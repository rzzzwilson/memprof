#!/usr/bin/env python3

"""
Test of "comprehension" string concatenation.
"""

import time
import common


start = time.time()
a = [str(n) for n in range(common.loops)]
a = ''.join(a)

print(f'comprehension|{common.loops}|{time.time() - start}')
