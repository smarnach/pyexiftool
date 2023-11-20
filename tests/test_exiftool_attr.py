# -*- coding: utf-8 -*-
"""
Test :: ExifTool base class - misc attribute validation tests
"""

# standard
import unittest
from pathlib import Path

# test helpers
from tests.common_util import TEST_IMAGE_JPG

# custom
import exiftool
from exiftool.exceptions import ExifToolRunning, ExifToolNotRunning


class TestExifToolAttrValidation(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifTool(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if self.et.running:
			self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_running_attribute(self):
		# test if we can read "running" but can't set it
		self.assertFalse(self.et.running)
		with self.assertRaises(AttributeError):
			self.et.running = True


	# ---------------------------------------------------------------------------------------------------------
	def test_executable_attribute(self):
		# test if we can read "running" but can't set it
		self.assertFalse(self.et.running)
		self.et.run()
		self.assertTrue(self.et.running)

		# if it's running, the executable has to exist (test coverage on reading the property)
		e = self.et.executable
		self.assertTrue(Path(e).exists())

		with self.assertRaises(ExifToolRunning):
			self.et.executable = "foo.bar"
		self.et.terminate()

		with self.assertRaises(FileNotFoundError):
			self.et.executable = "foo.bar"

		# specify the executable explicitly with the one known to exist (test coverage)
		self.et.executable = e
		self.assertEqual(self.et.executable, e)  # absolute path set should not change

		self.assertFalse(self.et.running)


	# ---------------------------------------------------------------------------------------------------------
	def test_blocksize_attribute(self):
		current = self.et.block_size

		# arbitrary
		self.et.block_size = 4
		self.assertEqual(self.et.block_size, 4)

		with self.assertRaises(ValueError):
			self.et.block_size = -1

		with self.assertRaises(ValueError):
			self.et.block_size = 0

		# restore
		self.et.block_size = current


	# ---------------------------------------------------------------------------------------------------------
	def test_encoding_attribute(self):
		current = self.et.encoding

		self.et.run()

		# cannot set when running
		with self.assertRaises(ExifToolRunning):
			self.et.encoding = "foo.bar"
		self.et.terminate()

		self.et.encoding = "foo"
		self.assertEqual(self.et.encoding, "foo")

		# restore
		self.et.encoding = current


	# ---------------------------------------------------------------------------------------------------------
	def test_common_args_attribute(self):

		self.et.run()
		with self.assertRaises(ExifToolRunning):
			self.et.common_args = []


	# ---------------------------------------------------------------------------------------------------------
	def test_version_attribute(self):
		self.et.run()
		# no error
		a = self.et.version

		self.et.terminate()

		# version is invalid when not running
		with self.assertRaises(ExifToolNotRunning):
			a = self.et.version


	# ---------------------------------------------------------------------------------------------------------
	def test_laststdout_attr(self):
		""" is the attribute available after a run? """
		self.et.run()

		stdo = self.et.execute(str(TEST_IMAGE_JPG))
		stde = self.et.last_stderr

		self.et.terminate()

		self.assertFalse(self.et.running)

		self.assertEqual(self.et.last_stdout, stdo)
		self.assertEqual(self.et.last_stderr, stde)


	# ---------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
