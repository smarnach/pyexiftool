# -*- coding: utf-8 -*-
"""
Test :: ExifTool base class - misc tests
"""

# standard
import unittest
import warnings
from pathlib import Path

# test helpers
from tests.common_util import TEST_IMAGE_JPG

# custom
import exiftool
from exiftool.exceptions import ExifToolNotRunning


class TestExifToolMisc(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifTool(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if self.et.running:
			self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_get_version_protected(self):
		""" test the protected method which can't be called when exiftool not running """
		self.assertFalse(self.et.running)
		self.assertRaises(ExifToolNotRunning, self.et._parse_ver)


	# ---------------------------------------------------------------------------------------------------------
	def test_invalid_args_list(self):
		# test to make sure passing in an invalid args list will cause it to error out
		with self.assertRaises(TypeError):
			exiftool.ExifTool(common_args="not a list")


	# ---------------------------------------------------------------------------------------------------------
	def test_common_args(self):
		# test to make sure passing in an invalid args list will cause it to error out
		with self.assertRaises(TypeError):
			exiftool.ExifTool(common_args={})

		# set to common_args=None == []
		self.assertEqual(exiftool.ExifTool(common_args=None).common_args, [])


	# ---------------------------------------------------------------------------------------------------------
	def test_run_twice(self):
		""" test that a UserWarning is thrown when run() is called twice """
		self.assertFalse(self.et.running)
		self.et.run()

		with warnings.catch_warnings(record=True) as w:
			self.assertTrue(self.et.running)
			self.et.run()
			self.assertEqual(len(w), 1)
			self.assertTrue(issubclass(w[0].category, UserWarning))


	# ---------------------------------------------------------------------------------------------------------
	def test_execute_types(self):
		""" test execute with different types """
		self.assertFalse(self.et.running)
		self.et.run()

		# no error with str
		self.et.execute("-ver")

		# no error with bytes
		self.et.execute(b"-ver")

		# no error with str
		self.et.execute(str(TEST_IMAGE_JPG))

		# error with Path
		with self.assertRaises(TypeError):
			self.et.execute(Path(TEST_IMAGE_JPG))


	# ---------------------------------------------------------------------------------------------------------






# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
