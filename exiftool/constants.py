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


# specify the extension so exiftool doesn't default to running "exiftool.py" on windows (which could happen)
if sys.platform == 'win32':
	DEFAULT_EXECUTABLE = "exiftool.exe"
else:
	DEFAULT_EXECUTABLE = "exiftool"
"""The name of the executable to run.

If the executable is not located in one of the paths listed in the
``PATH`` environment variable, the full path should be given here.
"""


SW_FORCEMINIMIZE = 11 # from win32con
