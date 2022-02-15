# -*- coding: utf-8 -*-

import unittest
import exiftool
import shutil
import tempfile
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent
PERSISTENT_TMP_DIR = False  # if set to true, will not delete temp dir on exit (useful for debugging output)

# Find example image.
EXAMPLE_FILE = SCRIPT_PATH / "rose.jpg"



class InitializationTest(unittest.TestCase):
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

	def test_read_all_from_nonexistent_file(self):
		"""
		`get_metadata`/`get_tags` raises an error if None comes back from execute_json()

		ExifToolHelper DOES NOT check each individual file in the list for existence.  If you pass invalid files to exiftool, undefined behavior can occur
		"""
		with self.assertRaises(RuntimeError):
			self.exif_tool_helper.get_metadata(['foo.bar'])

		with self.assertRaises(RuntimeError):
			self.exif_tool_helper.get_tags('foo.bar', 'DateTimeOriginal')



class TestExifToolHelper(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if hasattr(self, "et"):
			self.et.terminate()

	# ---------------------------------------------------------------------------------------------------------

	def test_terminate(self):
		self.et.terminate()
		# no warnings good

	# ---------------------------------------------------------------------------------------------------------
	def test_get_tags(self):
		"""
		`get_metadata`/`get_tags` should return an error when no files specified.
		"""

		with self.assertRaises(ValueError):
			# files can't be None
			self.et.get_tags(None, None)
			self.et.get_tags([], None)

	# ---------------------------------------------------------------------------------------------------------
	def test_invalid_tags_arg(self):
		with self.assertRaises(TypeError):
			self.et.get_tags(EXAMPLE_FILE, object())



	# ---------------------------------------------------------------------------------------------------------
	def test_auto_start(self):

		# test that a RuntimeError gets thrown if auto_start is false
		self.et = exiftool.ExifToolHelper(auto_start=False)
		with self.assertRaises(RuntimeError):
			self.et.get_metadata(EXAMPLE_FILE)

		# test that no errors returned if auto_start=True
		self.et = exiftool.ExifToolHelper(auto_start=True)
		metadata = self.et.get_metadata(EXAMPLE_FILE)
		self.assertEqual(type(metadata), list)


	# ---------------------------------------------------------------------------------------------------------

	def test_get_tags_params(self):
		""" test params argument """
		# lots of metadata on the file
		full_metadata = self.et.get_metadata(EXAMPLE_FILE)[0]

		# use params to get tag (basically using params to specify a tag)
		param_metadata = self.et.get_metadata(EXAMPLE_FILE, params="-XMPToolkit")[0]

		# the list should be significantly smaller
		self.assertGreater(len(full_metadata), len(param_metadata))


		param_metadata = self.et.get_metadata(EXAMPLE_FILE, params=["-XMPToolkit"])[0]
		self.assertGreater(len(full_metadata), len(param_metadata))


		with self.assertRaises(TypeError):
			# test invalid
			self.et.get_metadata(EXAMPLE_FILE, params=object())


	# ---------------------------------------------------------------------------------------------------------



# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
