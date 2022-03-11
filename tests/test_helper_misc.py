# -*- coding: utf-8 -*-
"""
Test :: ExifToolHelper - misc tests
"""

# standard
import unittest

# custom
import exiftool


class InitializationTest(unittest.TestCase):
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
if __name__ == '__main__':
	unittest.main()
