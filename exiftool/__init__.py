# -*- coding: utf-8 -*-

# version number using Semantic Versioning 2.0.0 https://semver.org/
# may not be PEP-440 compliant https://www.python.org/dev/peps/pep-0440/#semantic-versioning
__version__ = "0.5.0-alpha.0"

# make all of the original exiftool stuff available in this namespace
from .exiftool import ExifTool
from .helper import ExifToolHelper
from .experimental import ExifToolAlpha


# an old feature of the original class that exposed this variable at the library level
# TODO may remove and deprecate at a later time
from .constants import DEFAULT_EXECUTABLE
