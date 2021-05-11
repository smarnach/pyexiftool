# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import exiftool
import warnings
#import os
import shutil
import sys

from pathlib import Path

TMP_DIR = Path(__file__).parent / 'tmp'


class InitializationTest(unittest.TestCase):
	@unittest.expectedFailure
	def test_initialization(self):
		"""
		Initialization with all arguments at their default values.
		"""
		exif_tool_helper = exiftool.ExifToolHelper()
		exif_tool_helper.run()


class ReadingTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.exif_tool_helper = exiftool.ExifToolHelper(common_args=['-G', '-n', '-overwrite_original'])
		cls.exif_tool_helper.run()

	@unittest.expectedFailure
	def test_read_all_from_no_file(self):
		"""
		Supposedly, `get_metadata` always returns a list.
		"""
		metadata = self.exif_tool_helper.get_metadata([])
		self.assertEqual(metadata, [])

	@unittest.expectedFailure
	def test_read_all_from_nonexistent_file(self):
		"""
		Supposedly, `get_metadata` always returns a list.
		"""
		metadata = self.exif_tool_helper.get_metadata(['foo.bar'])
		self.assertEqual(metadata, [])

	@unittest.expectedFailure
	def test_read_tag_from_nonexistent_file(self):
		"""
		Confronted with a nonexistent file, `get_tag` should probably return None (as the tag is not found) or raise an
		appropriate exception.
		"""
		result = self.exif_tool_helper.get_tag('DateTimeOriginal', 'foo.bar')
		self.assertIsNone(result)


class TestExifToolHelper(unittest.TestCase):

	#---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if hasattr(self, "et"):
			if self.et.running:
				self.et.terminate()
		if hasattr(self, "process"):
			if self.process.poll() is None:
				self.process.terminate()

	#---------------------------------------------------------------------------------------------------------
	def test_get_metadata(self):
		expected_data = [{"SourceFile": "rose.jpg",
						  "File:FileType": "JPEG",
						  "File:ImageWidth": 70,
						  "File:ImageHeight": 46,
						  "XMP:Subject": "Röschen",
						  "Composite:ImageSize": "70 46"}, # older versions of exiftool used to display 70x46
						 {"SourceFile": "skyblue.png",
						  "File:FileType": "PNG",
						  "PNG:ImageWidth": 64,
						  "PNG:ImageHeight": 64,
						  "Composite:ImageSize": "64 64"}] # older versions of exiftool used to display 64x64
		script_path = Path(__file__).parent
		source_files = []

		for d in expected_data:
			d["SourceFile"] = f = script_path / d["SourceFile"]
			self.assertTrue(f.exists())
			source_files.append(str(f))
		with self.et:
			actual_data = self.et.get_metadata(source_files)
			tags0 = self.et.get_tags(["XMP:Subject"], source_files[0])[0]
			tag0 = self.et.get_tag("XMP:Subject", source_files[0])
		for expected, actual in zip(expected_data, actual_data):
			et_version = actual["ExifTool:ExifToolVersion"]
			self.assertTrue(isinstance(et_version, float))
			if isinstance(et_version, float):    # avoid exception in Py3k
				self.assertTrue(
					et_version >= 8.40, # TODO there's probably a bug in this test, 8.40 == 8.4 which isn't the intended behavior
					"you should at least use ExifTool version 8.40")
			actual["SourceFile"] = Path(actual["SourceFile"]).resolve()
			for k, v in expected.items():
				self.assertEqual(actual[k], v)
		tags0["SourceFile"] = Path(tags0["SourceFile"]).resolve()
		self.assertEqual(tags0, dict((k, expected_data[0][k])
									 for k in ["SourceFile", "XMP:Subject"]))
		self.assertEqual(tag0, "Röschen")

	#---------------------------------------------------------------------------------------------------------
	def test_set_metadata(self):
		mod_prefix = "newcap_"
		expected_data = [{"SourceFile": "rose.jpg",
						  "Caption-Abstract": "Ein Röschen ganz allein"},
						 {"SourceFile": "skyblue.png",
						  "Caption-Abstract": "Blauer Himmel"}]
		script_path = Path(__file__).parent
		source_files = []

		for d in expected_data:
			d["SourceFile"] = f = script_path / d["SourceFile"]
			self.assertTrue(f.exists())

			f_mod = TMP_DIR / (mod_prefix + f.name)
			f_mod_str = str(f_mod)

			self.assertFalse(f_mod.exists(), "%s should not exist before the test. Please delete." % f_mod)
			shutil.copyfile(f, f_mod)
			source_files.append(f_mod)
			with self.et:
				self.et.set_tags({"Caption-Abstract":d["Caption-Abstract"]}, f_mod_str)
				tag0 = self.et.get_tag("IPTC:Caption-Abstract", f_mod_str)
			f_mod.unlink()
			self.assertEqual(tag0, d["Caption-Abstract"])

	#---------------------------------------------------------------------------------------------------------
	def test_set_keywords(self):
		kw_to_add = ["added"]
		mod_prefix = "newkw_"
		expected_data = [{"SourceFile": "rose.jpg",
						  "Keywords": ["nature", "red plant"]}]
		script_path = Path(__file__).parent
		source_files = []
		
		for d in expected_data:
			d["SourceFile"] = f = script_path / d["SourceFile"]
			self.assertTrue(f.exists())
			f_mod = TMP_DIR / (mod_prefix + f.name)
			f_mod_str = str(f_mod)
			self.assertFalse(f_mod.exists(), "%s should not exist before the test. Please delete." % f_mod)

			shutil.copyfile(f, f_mod)
			source_files.append(f_mod)
			with self.et:
				self.et.set_keywords(exiftool.helper.KW_REPLACE, d["Keywords"], f_mod_str)
				kwtag0 = self.et.get_tag("IPTC:Keywords", f_mod_str)
				kwrest = d["Keywords"][1:]
				self.et.set_keywords(exiftool.helper.KW_REMOVE, kwrest, f_mod_str)
				kwtag1 = self.et.get_tag("IPTC:Keywords", f_mod_str)
				self.et.set_keywords(exiftool.helper.KW_ADD, kw_to_add, f_mod_str)
				kwtag2 = self.et.get_tag("IPTC:Keywords", f_mod_str)
			f_mod.unlink()
			self.assertEqual(kwtag0, d["Keywords"])
			self.assertEqual(kwtag1, d["Keywords"][0])
			self.assertEqual(kwtag2, [d["Keywords"][0]] + kw_to_add)


	#---------------------------------------------------------------------------------------------------------
	"""
	# TODO: write a test that covers keywords in set_tags_batch() and not using the keywords functionality directly
	def test_set_list_keywords(self):
		mod_prefix = "newkw_"
		expected_data = [{"SourceFile": "rose.jpg",
						  "Keywords": ["nature", "red plant"]}]
		script_path = Path(__file__).parent
		source_files = []

		for d in expected_data:
			d["SourceFile"] = f = script_path / d["SourceFile"]
			self.assertTrue(f.exists())
			f_mod = TMP_DIR / (mod_prefix + f.name)
			f_mod_str = str(f_mod)
			self.assertFalse(f_mod.exists(), "%s should not exist before the test. Please delete." % f_mod)

			shutil.copyfile(f, f_mod)
			source_files.append(f_mod)

			with self.et:
				self.et.set_keywords(exiftool.helper.KW_REPLACE, d["Keywords"], f_mod_str)
				kwtag0 = self.et.get_tag("IPTC:Keywords", f_mod_str)
				kwrest = d["Keywords"][1:]
				self.et.set_keywords(exiftool.helper.KW_REMOVE, kwrest, f_mod_str)
				kwtag1 = self.et.get_tag("IPTC:Keywords", f_mod_str)
				self.et.set_keywords(exiftool.helper.KW_ADD, kw_to_add, f_mod_str)
				kwtag2 = self.et.get_tag("IPTC:Keywords", f_mod_str)
			f_mod.unlink()
			self.assertEqual(kwtag0, d["Keywords"])
			self.assertEqual(kwtag1, d["Keywords"][0])
			self.assertEqual(kwtag2, [d["Keywords"][0]] + kw_to_add)
	"""

#---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
