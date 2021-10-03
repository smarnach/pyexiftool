# -*- coding: utf-8 -*-

import unittest
import exiftool
import shutil
import tempfile
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent
PERSISTENT_TMP_DIR = False  # if set to true, will not delete temp dir on exit (useful for debugging output)


class TestExifToolHelper(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if hasattr(self, "et"):
			if self.et.running:
				self.et.terminate()
		if hasattr(self, "process"):
			if self.process.poll() is None:
				self.process.terminate()


# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
