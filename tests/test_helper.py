# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import exiftool
import warnings
import os
import shutil
import sys

class TestExifToolHelper(unittest.TestCase):

	#---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])
	def tearDown(self):
		if hasattr(self, "et"):
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
		script_path = os.path.dirname(__file__)
		source_files = []
		for d in expected_data:
			d["SourceFile"] = f = os.path.join(script_path, d["SourceFile"])
			self.assertTrue(os.path.exists(f))
			source_files.append(f)
		with self.et:
			actual_data = self.et.get_metadata(source_files)
			tags0 = self.et.get_tags(["XMP:Subject"], source_files[0])[0]
			tag0 = self.et.get_tag("XMP:Subject", source_files[0])
		for expected, actual in zip(expected_data, actual_data):
			et_version = actual["ExifTool:ExifToolVersion"]
			self.assertTrue(isinstance(et_version, float))
			if isinstance(et_version, float):    # avoid exception in Py3k
				self.assertTrue(
					et_version >= 8.40,
					"you should at least use ExifTool version 8.40")
			actual["SourceFile"] = os.path.normpath(actual["SourceFile"])
			for k, v in expected.items():
				self.assertEqual(actual[k], v)
		tags0["SourceFile"] = os.path.normpath(tags0["SourceFile"])
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
		script_path = os.path.dirname(__file__)
		source_files = []
		for d in expected_data:
			d["SourceFile"] = f = os.path.join(script_path, d["SourceFile"])
			self.assertTrue(os.path.exists(f))
			f_mod = os.path.join(os.path.dirname(f), mod_prefix + os.path.basename(f))
			self.assertFalse(os.path.exists(f_mod), "%s should not exist before the test. Please delete." % f_mod)
			shutil.copyfile(f, f_mod)
			source_files.append(f_mod)
			with self.et:
				self.et.set_tags({"Caption-Abstract":d["Caption-Abstract"]}, f_mod)
				tag0 = self.et.get_tag("IPTC:Caption-Abstract", f_mod)
			os.remove(f_mod)
			self.assertEqual(tag0, d["Caption-Abstract"])

	#---------------------------------------------------------------------------------------------------------
	def test_set_keywords(self):
		kw_to_add = ["added"]
		mod_prefix = "newkw_"
		expected_data = [{"SourceFile": "rose.jpg",
						  "Keywords": ["nature", "red plant"]}]
		script_path = os.path.dirname(__file__)
		source_files = []
		for d in expected_data:
			d["SourceFile"] = f = os.path.join(script_path, d["SourceFile"])
			self.assertTrue(os.path.exists(f))
			f_mod = os.path.join(os.path.dirname(f), mod_prefix + os.path.basename(f))
			self.assertFalse(os.path.exists(f_mod), "%s should not exist before the test. Please delete." % f_mod)
			shutil.copyfile(f, f_mod)
			source_files.append(f_mod)
			with self.et:
				self.et.set_keywords(exiftool.helper.KW_REPLACE, d["Keywords"], f_mod)
				kwtag0 = self.et.get_tag("IPTC:Keywords", f_mod)
				kwrest = d["Keywords"][1:]
				self.et.set_keywords(exiftool.helper.KW_REMOVE, kwrest, f_mod)
				kwtag1 = self.et.get_tag("IPTC:Keywords", f_mod)
				self.et.set_keywords(exiftool.helper.KW_ADD, kw_to_add, f_mod)
				kwtag2 = self.et.get_tag("IPTC:Keywords", f_mod)
			os.remove(f_mod)
			self.assertEqual(kwtag0, d["Keywords"])
			self.assertEqual(kwtag1, d["Keywords"][0])
			self.assertEqual(kwtag2, [d["Keywords"][0]] + kw_to_add)


#---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
