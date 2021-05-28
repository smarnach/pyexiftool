# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import exiftool
import warnings
#import os
import shutil
import sys
#import tempfile
from pathlib import Path

TMP_DIR = Path(__file__).resolve().parent / 'tmp'

class TestTagCopying(unittest.TestCase):
	def setUp(self):
		# Prepare exiftool.
		self.exiftool = exiftool.ExifToolHelper()
		self.exiftool.run()

		# Prepare temporary directory for copy.
		#directory = tempfile.mkdtemp(prefix='exiftool-test-') # this requires cleanup or else it remains on the system in the $TEMP or %TEMP% directories
		directory = TMP_DIR

		# Find example image.
		this_path = Path(__file__).resolve().parent
		self.tag_source = str(this_path / 'rose.jpg')

		# Prepare path of copy.
		self.tag_target = str(directory / 'rose-tagcopy.jpg')

		# Copy image.
		shutil.copyfile(self.tag_source, self.tag_target)

		# Clear tags in copy.
		params = ['-overwrite_original', '-all=', self.tag_target]
		params_utf8 = [x.encode('utf-8') for x in params]
		self.exiftool.execute(*params_utf8)

	def test_tag_copying(self):
		tag = 'XMP:Subject'
		expected_value = 'Röschen'

		# Ensure source image has correct tag.
		original_value = self.exiftool.get_tag(tag, self.tag_source)
		self.assertEqual(original_value, expected_value)

		# Ensure target image does not already have that tag.
		value_before_copying = self.exiftool.get_tag(tag, self.tag_target)
		self.assertNotEqual(value_before_copying, expected_value)

		# Copy tags.
		self.exiftool.copy_tags(self.tag_source, self.tag_target)

		value_after_copying = self.exiftool.get_tag(tag, self.tag_target)
		self.assertEqual(value_after_copying, expected_value)

		self.exiftool.terminate()  # do it explictly for Windows, or else will hang on exit (CPython interpreter exit bug)


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
						  "Composite:ImageSize": "70 46"},  # older versions of exiftool used to display 70x46
						 {"SourceFile": "skyblue.png",
						  "File:FileType": "PNG",
						  "PNG:ImageWidth": 64,
						  "PNG:ImageHeight": 64,
						  "Composite:ImageSize": "64 64"}]  # older versions of exiftool used to display 64x64
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
					et_version >= 8.40,  # TODO there's probably a bug in this test, 8.40 == 8.4 which isn't the intended behavior
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
