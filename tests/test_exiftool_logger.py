# -*- coding: utf-8 -*-
"""
Test :: ExifTool base class - logger tests
"""

# standard
import unittest
import logging

# custom
import exiftool



class TestExifToolLogger(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifTool(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if self.et.running:
			self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_logger(self):
		""" TODO improve this test, currently very rudimentary """
		log = logging.getLogger("log_test")
		#log.level = logging.WARNING

		#logpath = TMP_DIR / 'exiftool_test.log'
		#fh = logging.FileHandler(logpath)

		#log.addHandler(fh)

		self.et.logger = log
		# no errors

		log = "bad log" # not a logger object
		with self.assertRaises(TypeError):
			self.et.logger = log

		self.et.run()  # get some coverage by doing stuff




# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
