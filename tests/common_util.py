# -*- coding: utf-8 -*-

"""
This file contains some common utility functions which are used by multiple tests

Having it all in one place makes things easier to fix, and less duplicate code
"""

from pathlib import Path
import tempfile
import os

from typing import Optional, Tuple, Any

# ---------------------------------------------------------------------------------------------------------

# default is False.  Change here to have all tests persist their output... then change it back to False before committing!
PERSISTENT_TMP_DIR: bool = False
"""if set to true, will not delete temp dir after tests (useful for debugging test output)"""


SCRIPT_PATH = Path(__file__).resolve().parent

# location to images directory
TEST_IMAGE_DIR = SCRIPT_PATH / "files"


# Find example image (note: JPG is listed explicitly, as it may have different tags than other file types)
# listed here in common so that if the path changes, just change it here
TEST_IMAGE_JPG = TEST_IMAGE_DIR / "rose.jpg"


# ---------------------------------------------------------------------------------------------------------

def et_get_temp_dir(suffix: Optional[str] = None, base_path: Optional[Path] = None, persist: Optional[bool] = None) -> Tuple[Optional[Any], Path]:
	"""
	suffix is optional str to append to the temp dir creation.  This is useful to figure out which test created the output folder
	base_path is optional Path to point to the path where the temp dir is to be created.  None=SCRIPT_PATH
	persist is optional bool.  If set to a value, this method will honor that value.  None = use default up above (useful if you're writing a particular test and you only want that one to persist when testing)

	returns (temp_obj, temp_dir)

	temp_obj = Object which needs to be saved somewhere or else the TemporaryDirectory gets garbage collected
	temp_dir = Path() of the temp dir returned
	"""
	# Prepare temporary directory for file modifications.
	prefix = "exiftool-tmp-"

	kwargs = {
		"prefix": prefix if suffix is None else f"{prefix}{suffix}-",
		"dir": SCRIPT_PATH if base_path is None else base_path,
	}

	# if not specified, take default, else take what was given
	do_persist = PERSISTENT_TMP_DIR if persist is None else persist

	# mkdtemp requires cleanup or else it remains on the system
	if do_persist:
		temp_obj = None
		temp_dir = Path(tempfile.mkdtemp(**kwargs))
	else:
		# have to save the object or else garbage collection cleans it up and dir gets deleted
		# https://simpleit.rocks/python/test-files-creating-a-temporal-directory-in-python-unittests/
		temp_obj = tempfile.TemporaryDirectory(**kwargs)
		temp_dir = Path(temp_obj.name)

	return (temp_obj, temp_dir)

# ---------------------------------------------------------------------------------------------------------


def create_random_bin_file(filepath: Path, size: int):
	"""
	generate random binary file with the specified size in bytes

	:param filename: the filename
	:param size: the size in bytes

	:return: filepath
	"""
	# https://www.bswen.com/2018/04/python-How-to-generate-random-large-file-using-python.html

	if filepath.exists():
		raise FileExistsError

	with open(filepath, 'wb') as f:
		f.write(os.urandom(size))

	return filepath

# ---------------------------------------------------------------------------------------------------------

