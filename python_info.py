"""
Little program to get python version and platform info.

Designed to write results to "stdout".
"""

import platform

print('Python %s on %s' % (platform.python_version().strip(), platform.platform().strip()))
