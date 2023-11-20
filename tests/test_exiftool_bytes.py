# -*- coding: utf-8 -*-
"""
Test :: ExifTool base class - execute() using raw_bytes parameter
"""

# standard
import unittest
import shutil

# test helpers
from tests.common_util import et_get_temp_dir, TEST_IMAGE_DIR, TEST_IMAGE_JPG, create_random_bin_file

# custom
import exiftool

class TestExifToolBytes(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifTool(common_args=["-G", "-n", "-overwrite_original"], config_file=TEST_IMAGE_DIR / "my_makernotes.config")

		(self.temp_obj, self.temp_dir) = et_get_temp_dir(suffix="etbytes")

	def tearDown(self):
		if self.et.running:
			self.et.terminate()

	# ---------------------------------------------------------------------------------------------------------

	def test_read_write_binary(self):
		""" test reading and writing binary data """
		self.assertFalse(self.et.running)
		self.et.run()

		### set up files ###

		# write a binary file to test with ... we can make it random or the same, shouldn't matter
		BIN_FILE_SIZE = 1024

		p_bin_file = self.temp_dir / "test_data.bin"
		create_random_bin_file(p_bin_file, BIN_FILE_SIZE)

		p_jpg_file = self.temp_dir / "rose.jpg"
		shutil.copyfile(TEST_IMAGE_JPG, p_jpg_file)

		### write the binary data ###
		self.et.execute(f"-MyMakerNotes<={p_bin_file}", str(p_jpg_file))
		self.assertEqual(self.et.last_status, 0)

		### read the binary data and compare ###
		with open(p_bin_file, 'rb') as f:
			bin_file_data = f.read()

		# make sure it's the right amount of bytes wrote in originally
		self.assertEqual(len(bin_file_data), BIN_FILE_SIZE)

		# get the custom tag
		written_bin_data = self.et.execute("-b", "-MyMakerNotes", str(p_jpg_file), raw_bytes=True)

		# check that they are equal
		self.assertEqual(bin_file_data, written_bin_data)




# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
