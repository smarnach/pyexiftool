# -*- coding: utf-8 -*-
"""
Test :: ExifToolHelper - misc tests
"""

# standard
import unittest
from pathlib import Path

# test helpers
from tests.common_util import TEST_IMAGE_JPG

# custom
import exiftool


class HelperInitializationTest(unittest.TestCase):
	def test_initialization(self):
		"""
		Initialization with all arguments at their default values.

		this is to test that the constructor passes the right values to the base class (ensure that the class inheritence working as expected even if underlying base class parameters change)
		"""
		exif_tool_helper = exiftool.ExifToolHelper()
		exif_tool_helper.run()

		self.assertTrue(exif_tool_helper.running)
		exif_tool_helper.terminate()
		self.assertFalse(exif_tool_helper.running)


# ---------------------------------------------------------------------------------------------------------

class TestExifToolHelperMisc(unittest.TestCase):
	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if self.et.running:
			self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_execute_types(self):
		""" test execute with different types (exact same as the test with ExifTool, except the last one passes) """
		self.assertFalse(self.et.running)

		# no error with str
		self.et.execute("-ver")

		# no error with bytes
		self.et.execute(b"-ver")

		# no error with str
		self.et.execute(str(TEST_IMAGE_JPG))

		# error with Path
		self.et.execute(Path(TEST_IMAGE_JPG))


	# ---------------------------------------------------------------------------------------------------------



# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
