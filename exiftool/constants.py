# -*- coding: utf-8 -*-
# This file is part of PyExifTool.
#
# PyExifTool is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the licence, or
# (at your option) any later version, or the BSD licence.
#
# PyExifTool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING.GPL or COPYING.BSD for more details.

"""
This file defines constants which are used by others in the package
"""


import sys


##################################
############# HELPERS ############
##################################

# instead of comparing everywhere sys.platform, do it all here in the constants (less typo chances)
# True if Windows
PLATFORM_WINDOWS: bool = (sys.platform == 'win32')
# Prior to Python 3.3, the value for any Linux version is always linux2; after, it is linux.
# https://stackoverflow.com/a/13874620/15384838
PLATFORM_LINUX: bool = (sys.platform == 'linux' or sys.platform == 'linux2')



##################################
####### PLATFORM DEFAULTS ########
##################################


# specify the extension so exiftool doesn't default to running "exiftool.py" on windows (which could happen)
DEFAULT_EXECUTABLE: str

if PLATFORM_WINDOWS:
	DEFAULT_EXECUTABLE = "exiftool.exe"
else:  # pytest-cov:windows: no cover
	DEFAULT_EXECUTABLE = "exiftool"
"""The name of the executable to run.

If the executable is not located in one of the paths listed in the
``PATH`` environment variable, the full path should be given here.
"""



##################################
####### STARTUP CONSTANTS ########
##################################

# for Windows STARTUPINFO
SW_FORCEMINIMIZE: int = 11  # from win32con

# for Linux preexec_fn
PR_SET_PDEATHSIG: int = 1  # taken from linux/prctl.h



##################################
######## GLOBAL DEFAULTS #########
##################################

# The default block size when reading from exiftool.  The standard value
# should be fine, though other values might give better performance in
# some cases.
DEFAULT_BLOCK_SIZE: int = 4096

# this is the minimum version required at this time
# 8.40 / 8.60 (production): implemented the -stay_open flag
# 12.10 / 12.15 (production): implemented exit status on -echo4
EXIFTOOL_MINIMUM_VERSION = "12.15"
