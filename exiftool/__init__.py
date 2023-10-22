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
PyExifTool is a Python library to communicate with an instance of Phil
Harvey's excellent ExifTool_ command-line application.  The library
provides the class :py:class:`ExifTool` that runs the command-line
tool in batch mode and features methods to send commands to that
program, including methods to extract meta-information from one or
more image files.  Since ``exiftool`` is run in batch mode, only a
single instance needs to be launched and can be reused for many
queries.  This is much more efficient than launching a separate
process for every single query.

.. _ExifTool: https://exiftool.org

The source code can be checked out from the github repository with

::

	git clone git://github.com/sylikc/pyexiftool.git

Alternatively, you can download a tarball_.  There haven't been any
releases yet.

.. _tarball: https://github.com/sylikc/pyexiftool/tarball/master

PyExifTool is licenced under GNU GPL version 3 or later, or BSD license.

Example usage::

	import exiftool

	files = ["a.jpg", "b.png", "c.tif"]
	with exiftool.ExifToolHelper() as et:
		metadata = et.get_metadata(files)
	for d in metadata:
		print("{:20.20} {:20.20}".format(d["SourceFile"],
                                         d["EXIF:DateTimeOriginal"]))

"""

# version number using Semantic Versioning 2.0.0 https://semver.org/
# may not be PEP-440 compliant https://www.python.org/dev/peps/pep-0440/#semantic-versioning
__version__ = "0.5.6"


# while we COULD import all the exceptions into the base library namespace,
# it's best that it lives as exiftool.exceptions, to not pollute the base namespace
from . import exceptions


# make all of the original exiftool stuff available in this namespace
from .exiftool import ExifTool
from .helper import ExifToolHelper
from .experimental import ExifToolAlpha

# an old feature of the original class that exposed this variable at the library level
# TODO may remove and deprecate at a later time
#from .constants import DEFAULT_EXECUTABLE
