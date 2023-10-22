# -*- coding: utf-8 -*-
#
# This file is part of PyExifTool.
#
# PyExifTool <http://github.com/sylikc/pyexiftool>
#
# Copyright 2019-2023 Kevin M (sylikc)
# Copyright 2012-2014 Sven Marnach
#
# Community contributors are listed in the CHANGELOG.md for the PRs
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

This submodule defines constants which are used by other modules in the package

"""

import sys


##################################
############# HELPERS ############
##################################

# instead of comparing everywhere sys.platform, do it all here in the constants (less typo chances)
# True if Windows
PLATFORM_WINDOWS: bool = (sys.platform == 'win32')
"""sys.platform check, set to True if Windows"""

# Prior to Python 3.3, the value for any Linux version is always linux2; after, it is linux.
# https://stackoverflow.com/a/13874620/15384838
PLATFORM_LINUX: bool = (sys.platform == 'linux' or sys.platform == 'linux2')
"""sys.platform check, set to True if Linux"""



##################################
####### PLATFORM DEFAULTS ########
##################################


# specify the extension so exiftool doesn't default to running "exiftool.py" on windows (which could happen)
DEFAULT_EXECUTABLE: str
"""The name of the default executable to run.

``exiftool`` (Linux) or ``exiftool.exe`` (Windows)

By default, the executable is searched for on one of the paths listed in the
``PATH`` environment variable.  If it's not on the ``PATH``, a full path should be given to the ExifTool constructor.
"""

if PLATFORM_WINDOWS:
	DEFAULT_EXECUTABLE = "exiftool.exe"
else:  # pytest-cov:windows: no cover
	DEFAULT_EXECUTABLE = "exiftool"



##################################
####### STARTUP CONSTANTS ########
##################################

# for Windows STARTUPINFO
SW_FORCEMINIMIZE: int = 11
"""Windows ShowWindow constant from win32con

Indicates the launched process window should start minimized
"""

# for Linux preexec_fn
PR_SET_PDEATHSIG: int = 1
"""Extracted from linux/prctl.h

Allows a kill signal to be sent to child processes when the parent unexpectedly dies
"""



##################################
######## GLOBAL DEFAULTS #########
##################################

DEFAULT_BLOCK_SIZE: int = 4096
"""The default block size when reading from exiftool.  The standard value
should be fine, though other values might give better performance in
some cases."""

EXIFTOOL_MINIMUM_VERSION = "12.15"
"""this is the minimum *exiftool* version required for current version of PyExifTool

* 8.40 / 8.60 (production): implemented the -stay_open flag
* 12.10 / 12.15 (production): implemented exit status on -echo4
"""
