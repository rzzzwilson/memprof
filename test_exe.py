#!/usr/bin/env python3

import sys
import time

a = ''
inc = 'abcdefghijklmnopqrstuvwxyz' * 1000
for _ in range(1000):
    a += inc
#    print(sys.getsizeof(a))
    time.sleep(0.01)
