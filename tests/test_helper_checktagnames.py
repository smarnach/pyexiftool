# -*- coding: utf-8 -*-
"""
Test :: ExifToolHelper - tag name validation tests
"""

# standard
import unittest
import shutil

# test helpers
from tests.common_util import et_get_temp_dir
from tests.common_util import TEST_IMAGE_JPG

# custom
import exiftool
from exiftool.exceptions import ExifToolOutputEmptyError, ExifToolTagNameError



class TagNameReadTest(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_check_tag_names(self):
		""" simple read test for tag names """

		with self.assertRaises(ExifToolTagNameError):
			self.et.get_tags(TEST_IMAGE_JPG, "-Comment")

		self.et.get_tags(TEST_IMAGE_JPG, "Comment#")

		with self.assertRaises(ExifToolTagNameError):
			self.et.get_tags(TEST_IMAGE_JPG, "Com#ment")

		# valid tags
		self.et.get_tags(TEST_IMAGE_JPG, "test:tag")
		self.et.get_tags(TEST_IMAGE_JPG, "*date*")

		# non-sensical, but even exiftool lets these slide with no errors
		self.et.get_tags(TEST_IMAGE_JPG, "C-o:m:m:ent#")
		self.et.get_tags(TEST_IMAGE_JPG, "Comment-")
		self.et.get_tags(TEST_IMAGE_JPG, "test:-tag")
		self.et.get_tags(TEST_IMAGE_JPG, "t-e-st:-tag---")

	# ---------------------------------------------------------------------------------------------------------




class TagNameWriteTest(unittest.TestCase):
	""" these tests are to ensure the robustness of the check_tag_names feature """

	@classmethod
	def setUp(self):
		self.et = exiftool.ExifToolHelper(
			common_args=["-G", "-n", "-overwrite_original"], encoding="UTF-8"
		)

		# standardize, all these need the example file copied to a temp directory
		(self.temp_obj, self.temp_dir) = et_get_temp_dir(suffix="tagname")

		self.test_file = self.temp_dir / "test_rose.jpg"

		shutil.copyfile(TEST_IMAGE_JPG, self.test_file)

	# ---------------------------------------------------------------------------------------------------------

	def test_write_comment(self):

		test_file = self.test_file
		my_tag = "File:Comment"
		my_comment = "foo.bar/comment"
		bad_comment = "lorem ipsum"

		self.et.set_tags(test_file, {my_tag: my_comment})

		self.assertEqual(my_comment, self.et.get_tags(test_file, my_tag)[0][my_tag])

		self.assertTrue(self.et.check_tag_names)
		with self.assertRaises(ExifToolTagNameError):
			# this was what the flag was meant to prevent
			self.et.get_tags(test_file, f"Comment={bad_comment}")

		self.assertEqual(my_comment, self.et.get_tags(test_file, my_tag)[0][my_tag])


		# turn off that tag check (this is what you DON'T WANT to happen)
		self.et.check_tag_names = False
		self.assertFalse(self.et.check_tag_names)
		with self.assertRaises(ExifToolOutputEmptyError):
			self.et.get_tags(test_file, f"Comment={bad_comment}")
		self.assertEqual(bad_comment, self.et.get_tags(test_file, my_tag)[0][my_tag])


		self.et.check_tag_names = True


	# ---------------------------------------------------------------------------------------------------------

	def test_tag_name_hyphen(self):
		""" this is cited on some examples on exiftool's documentation

		this example also demonstrates how what you ask for as a tag isn't what you get back sometimes... the tag comes back in the case that's defined inside exiftool
		"""

		test_file = self.test_file
		my_tag = "xmp:description-de"
		my_value = "k&uuml;hl"

		# note how what you asked for isn't always what you get
		my_tag_case = "XMP:Description-de"
		my_utf8 = "kühl"

		self.et.set_tags(test_file, {my_tag: my_value}, params="-E")

		self.assertEqual(my_utf8, self.et.get_tags(test_file, my_tag)[0][my_tag_case])


	# ---------------------------------------------------------------------------------------------------------




# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
