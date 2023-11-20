# -*- coding: utf-8 -*-
"""
Test :: ExifToolHelper - get_metadata/get_tags tests
"""

# standard
import unittest
from pathlib import Path

# pip
from packaging import version

# test helpers
from tests.common_util import TEST_IMAGE_DIR, TEST_IMAGE_JPG

# custom
import exiftool
from exiftool.exceptions import ExifToolExecuteError



class TestHelperGetTags(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_get_tags_no_files(self):
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
			self.et.get_tags(TEST_IMAGE_JPG, object())


	# ---------------------------------------------------------------------------------------------------------
	def test_get_tags_params(self):
		""" test params argument """
		# lots of metadata on the file
		full_metadata = self.et.get_metadata(TEST_IMAGE_JPG)[0]

		# use params to get tag (basically using params to specify a tag)
		param_metadata = self.et.get_metadata(TEST_IMAGE_JPG, params="-XMPToolkit")[0]

		# the list should be significantly smaller
		self.assertGreater(len(full_metadata), len(param_metadata))


		param_metadata = self.et.get_metadata(TEST_IMAGE_JPG, params=["-XMPToolkit"])[0]
		self.assertGreater(len(full_metadata), len(param_metadata))


		# this class is an arbitrary object that returns a string
		class TestClass(object):
			def __str__(self):
				return "-n"

		# this is now permitted, params can be anything castable
		self.et.get_metadata(TEST_IMAGE_JPG, params=TestClass())


	# ---------------------------------------------------------------------------------------------------------
	def test_get_metadata_file_mixed_existence(self):
		"""
		this tests for errors behavior when some files exist, and others don't

		this is less of a test for the class itself but expected exit status interaction with exiftool
		"""
		# expected no error
		self.et.get_metadata(TEST_IMAGE_JPG)

		self.et.check_execute = False
		# expected no error
		self.et.get_metadata([TEST_IMAGE_JPG, "foo.bar"])

		# running same command with check_execute enabled
		self.et.check_execute = True
		with self.assertRaises(ExifToolExecuteError):
			self.et.get_metadata([TEST_IMAGE_JPG, "foo.bar"])


	# ---------------------------------------------------------------------------------------------------------
	def test_get_metadata(self):
		"""
		test that a read is returning expected data
		"""
		expected_data = [
			{
				"SourceFile": "rose.jpg",
				"File:FileType": "JPEG",
				"File:ImageWidth": 70,
				"File:ImageHeight": 46,
				"XMP:Subject": "Röschen",
				"Composite:ImageSize": "70 46",
			},
			{
				"SourceFile": "skyblue.png",
				"File:FileType": "PNG",
				"PNG:ImageWidth": 64,
				"PNG:ImageHeight": 64,
				"Composite:ImageSize": "64 64",
			},
		]
		source_files = []

		# encoding required for this to pass is UTF-8, that's because the compared strings are encoded in UTF-8 (this file is UTF-8)
		self.et.encoding = 'UTF-8'

		for d in expected_data:
			d["SourceFile"] = f = TEST_IMAGE_DIR / d["SourceFile"]
			self.assertTrue(f.exists())
			source_files.append(f)

		with self.et:
			actual_data = self.et.get_metadata(source_files)
			tags0 = self.et.get_tags(source_files[0], ["XMP:Subject"])[0]
			#tag0 = self.et.get_tag(source_files[0], "XMP:Subject")

		required_version = version.parse("8.40")
		for expected, actual in zip(expected_data, actual_data):
			actual_version = version.parse(str(actual["ExifTool:ExifToolVersion"]))
			self.assertGreaterEqual(actual_version, required_version)
			actual["SourceFile"] = Path(actual["SourceFile"]).resolve()
			for k, v in expected.items():
				self.assertEqual(actual[k], v)

		tags0["SourceFile"] = Path(tags0["SourceFile"]).resolve()
		self.assertEqual(
			tags0, dict((k, expected_data[0][k]) for k in ["SourceFile", "XMP:Subject"])
		)
		#self.assertEqual(tag0, expected_data[0]["XMP:Subject"])

	# ---------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
