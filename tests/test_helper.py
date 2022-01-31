# -*- coding: utf-8 -*-

import unittest
import exiftool
import shutil
import tempfile
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent
PERSISTENT_TMP_DIR = False  # if set to true, will not delete temp dir on exit (useful for debugging output)



class InitializationTest(unittest.TestCase):
	@unittest.expectedFailure
	def test_initialization(self):
		"""
		Initialization with all arguments at their default values.
		"""
		exif_tool_helper = exiftool.ExifToolHelper()
		exif_tool_helper.run()


class ReadingTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.exif_tool_helper = exiftool.ExifToolHelper(common_args=['-G', '-n', '-overwrite_original'])
		cls.exif_tool_helper.run()

	@unittest.expectedFailure
	def test_read_all_from_no_file(self):
		"""
		Supposedly, `get_metadata` always returns a list.
		"""
		metadata = self.exif_tool_helper.get_metadata([])
		self.assertEqual(metadata, [])

	@unittest.expectedFailure
	def test_read_all_from_nonexistent_file(self):
		"""
		Supposedly, `get_metadata` always returns a list.
		"""
		metadata = self.exif_tool_helper.get_metadata(['foo.bar'])
		self.assertEqual(metadata, [])

	@unittest.expectedFailure
	def test_read_tag_from_nonexistent_file(self):
		"""
		Confronted with a nonexistent file, `get_tag` should probably return None (as the tag is not found) or raise an
		appropriate exception.
		"""
		result = self.exif_tool_helper.get_tag('DateTimeOriginal', 'foo.bar')
		self.assertIsNone(result)


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
