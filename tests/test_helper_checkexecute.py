# -*- coding: utf-8 -*-
"""
Test :: ExifToolHelper - misc tests
"""

# standard
import unittest

# test helpers
from tests.common_util import et_get_temp_dir, TEST_IMAGE_JPG

# custom
import exiftool
from exiftool.exceptions import ExifToolOutputEmptyError, ExifToolJSONInvalidError, ExifToolExecuteError


class TestHelperCheckExecute(unittest.TestCase):
	@classmethod
	def setUp(self) -> None:
		self.eth = exiftool.ExifToolHelper(common_args=['-G', '-n', '-overwrite_original'])
		self.eth.run()

	def tearDown(self):
		self.eth.terminate()

	# ---------------------------------------------------------------------------------------------------------
	def test_read_all_from_nonexistent_file_no_checkexecute(self):
		"""
		`get_metadata`/`get_tags` raises an error if None comes back from execute_json()

		ExifToolHelper DOES NOT check each individual file in the list for existence.  If you pass invalid files to exiftool, undefined behavior can occur
		"""
		self.eth.check_execute = False

		with self.assertRaises(ExifToolOutputEmptyError):
			self.eth.get_metadata(['foo.bar'])

		with self.assertRaises(ExifToolOutputEmptyError):
			self.eth.get_tags('foo.bar', 'DateTimeOriginal')

	# ---------------------------------------------------------------------------------------------------------

	def test_read_all_from_nonexistent_file_yes_checkexecute(self):
		# run above test again with check_execute = True

		self.eth.check_execute = True

		with self.assertRaises(ExifToolExecuteError):
			self.eth.get_metadata(['foo.bar'])

		with self.assertRaises(ExifToolExecuteError):
			self.eth.get_tags('foo.bar', 'DateTimeOriginal')

	# ---------------------------------------------------------------------------------------------------------

	def test_w_flag(self):
		"""
		test passing a -w flag to write some output
		"""
		(temp_obj, temp_dir) = et_get_temp_dir(suffix="wflag")

		with self.assertRaises(ExifToolJSONInvalidError):
			self.eth.get_metadata(TEST_IMAGE_JPG, params=["-w", f"{temp_dir}/%f.txt"])

	# ---------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
