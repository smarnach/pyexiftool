# -*- coding: utf-8 -*-
"""
Test :: ExifToolHelper - Helper's start/run wrappers tests
"""

# standard
import unittest

# test helpers
from tests.common_util import TEST_IMAGE_JPG

# custom
import exiftool
from exiftool.exceptions import ExifToolNotRunning




class TestHelperRunWrappers(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_run(self):
		# no warnings when terminating when not running
		self.assertFalse(self.et.running)
		self.et.run()
		self.assertTrue(self.et.running)
		self.et.run()


	# ---------------------------------------------------------------------------------------------------------
	def test_terminate(self):
		# no warnings when terminating when not running
		self.assertFalse(self.et.running)
		self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_auto_start(self):

		# test that a RuntimeError gets thrown if auto_start is false
		self.et = exiftool.ExifToolHelper(auto_start=False)
		self.assertFalse(self.et.auto_start)
		with self.assertRaises(ExifToolNotRunning):
			self.et.get_metadata(TEST_IMAGE_JPG)

		# test that no errors returned if auto_start=True
		self.et = exiftool.ExifToolHelper(auto_start=True)
		self.assertTrue(self.et.auto_start)
		metadata = self.et.get_metadata(TEST_IMAGE_JPG)
		self.assertEqual(type(metadata), list)


	# ---------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
