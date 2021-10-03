# -*- coding: utf-8 -*-

# import as directory

# make all of the original exiftool stuff available in this namespace
from .exiftool import ExifTool
from .helper import ExifToolHelper
from .experimental import ExifToolAlpha


# an old feature of the original class that exposed this variable at the library level
# TODO may remove and deprecate at a later time
from .constants import DEFAULT_EXECUTABLE
