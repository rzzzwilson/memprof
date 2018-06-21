#!/usr/bin/env python3

import sys
import time

print('test_exe.py START')
a = ''
inc = 'abcdefghijklmnopqrstuvwxyz' * 1000
for _ in range(1000):
    a += inc
    time.sleep(0.01)
print('test_exe.py END')
