# -*- coding: utf-8 -*-

import unittest
import exiftool
from exiftool.exceptions import ExifToolNotRunning, OutputEmpty, OutputNotJSON, ExifToolExecuteError
import shutil
import tempfile
from pathlib import Path

from packaging import version

SCRIPT_PATH = Path(__file__).resolve().parent
PERSISTENT_TMP_DIR = False  # if set to true, will not delete temp dir on exit (useful for debugging output)

# Find example image.
EXAMPLE_FILE = SCRIPT_PATH / "rose.jpg"



class InitializationTest(unittest.TestCase):
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


		# Prepare temporary directory.
		kwargs = {"prefix": "exiftool-tmp-", "dir": SCRIPT_PATH}
		# mkdtemp requires cleanup or else it remains on the system
		if PERSISTENT_TMP_DIR:
			cls.temp_obj = None
			cls.tmp_dir = Path(tempfile.mkdtemp(**kwargs))
		else:
			# have to save the object or else garbage collection cleans it up and dir gets deleted
			cls.temp_obj = tempfile.TemporaryDirectory(**kwargs)
			cls.tmp_dir = Path(cls.temp_obj.name)

	# ---------------------------------------------------------------------------------------------------------

	def test_read_all_from_nonexistent_file_no_checkexecute(self):
		"""
		`get_metadata`/`get_tags` raises an error if None comes back from execute_json()

		ExifToolHelper DOES NOT check each individual file in the list for existence.  If you pass invalid files to exiftool, undefined behavior can occur
		"""
		check_value = self.exif_tool_helper.check_execute  # save off current setting

		self.exif_tool_helper.check_execute = False

		with self.assertRaises(OutputEmpty):
			self.exif_tool_helper.get_metadata(['foo.bar'])

		with self.assertRaises(OutputEmpty):
			self.exif_tool_helper.get_tags('foo.bar', 'DateTimeOriginal')

		self.exif_tool_helper.check_execute = check_value

	# ---------------------------------------------------------------------------------------------------------

	def test_read_all_from_nonexistent_file_yes_checkexecute(self):
		# run above test again and check_execute = True

		check_value = self.exif_tool_helper.check_execute  # save off current setting

		self.exif_tool_helper.check_execute = True

		with self.assertRaises(ExifToolExecuteError):
			self.exif_tool_helper.get_metadata(['foo.bar'])

		with self.assertRaises(ExifToolExecuteError):
			self.exif_tool_helper.get_tags('foo.bar', 'DateTimeOriginal')

		self.exif_tool_helper.check_execute = check_value

	# ---------------------------------------------------------------------------------------------------------

	def test_w_flag(self):
		"""
		test passing a -w flag to write some output
		"""
		with self.assertRaises(OutputNotJSON):
			self.exif_tool_helper.get_metadata(EXAMPLE_FILE, params=["-w", f"{self.tmp_dir}/%f.txt"])

	# ---------------------------------------------------------------------------------------------------------



class TestExifToolHelper(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if hasattr(self, "et"):
			self.et.terminate()

	# ---------------------------------------------------------------------------------------------------------

	def test_run(self):
		# no warnings when terminating when not running
		self.assertFalse(self.et.running)
		self.et.run()
		self.assertTrue(self.et.running)
		self.et.run()

	# ---------------------------------------------------------------------------------------------------------

	def test_terminate(self):
		# no warnings when terminating when not running
		self.assertFalse(self.et.running)
		self.et.terminate()

	# ---------------------------------------------------------------------------------------------------------
	def test_get_tags(self):
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
			self.et.get_tags(EXAMPLE_FILE, object())

	# ---------------------------------------------------------------------------------------------------------
	def test_auto_start(self):

		# test that a RuntimeError gets thrown if auto_start is false
		self.et = exiftool.ExifToolHelper(auto_start=False)
		with self.assertRaises(ExifToolNotRunning):
			self.et.get_metadata(EXAMPLE_FILE)

		# test that no errors returned if auto_start=True
		self.et = exiftool.ExifToolHelper(auto_start=True)
		metadata = self.et.get_metadata(EXAMPLE_FILE)
		self.assertEqual(type(metadata), list)

	# ---------------------------------------------------------------------------------------------------------
	def test_get_tags_params(self):
		""" test params argument """
		# lots of metadata on the file
		full_metadata = self.et.get_metadata(EXAMPLE_FILE)[0]

		# use params to get tag (basically using params to specify a tag)
		param_metadata = self.et.get_metadata(EXAMPLE_FILE, params="-XMPToolkit")[0]

		# the list should be significantly smaller
		self.assertGreater(len(full_metadata), len(param_metadata))


		param_metadata = self.et.get_metadata(EXAMPLE_FILE, params=["-XMPToolkit"])[0]
		self.assertGreater(len(full_metadata), len(param_metadata))


		with self.assertRaises(TypeError):
			# test invalid
			self.et.get_metadata(EXAMPLE_FILE, params=object())


	# ---------------------------------------------------------------------------------------------------------
	def test_get_metadata_file_mixed_existence(self):
		"""
		this tests for errors behavior when some files exist, and others don't

		this is less of a test for the class itself but expected exit status interaction with exiftool
		"""
		rose = SCRIPT_PATH / "rose.jpg"
		check_value = self.et.check_execute  # save off current setting

		# expected no error
		self.et.get_metadata(rose)

		self.et.check_execute = False
		# expected no error
		self.et.get_metadata([rose, "foo.bar"])

		# running same command with check_execute enabled
		self.et.check_execute = True
		with self.assertRaises(ExifToolExecuteError):
			self.et.get_metadata([rose, "foo.bar"])


		self.et.check_execute = check_value


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
			d["SourceFile"] = f = SCRIPT_PATH / d["SourceFile"]
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

class WritingTest(unittest.TestCase):
	@classmethod
	def setUp(self):
		self.et = exiftool.ExifToolHelper(
			common_args=["-G", "-n", "-overwrite_original"], encoding="UTF-8"
		)

		# Prepare temporary directory for copy.
		kwargs = {"prefix": "exiftool-tmp-", "dir": SCRIPT_PATH}
		if PERSISTENT_TMP_DIR:
			self.temp_obj = None
			self.tmp_dir = Path(tempfile.mkdtemp(**kwargs))
		else:
			self.temp_obj = tempfile.TemporaryDirectory(**kwargs)
			self.tmp_dir = Path(self.temp_obj.name)

	# ---------------------------------------------------------------------------------------------------------

	def test_set_tags(self):
		mod_prefix = "newcap_"
		expected_data = [
			{
				"SourceFile": "rose.jpg",
				"Caption-Abstract": "Ein Röschen ganz allein",
			},
			{"SourceFile": "skyblue.png", "Caption-Abstract": "Blauer Himmel"},
		]
		source_files = []

		for d in expected_data:
			d["SourceFile"] = f = SCRIPT_PATH / d["SourceFile"]
			self.assertTrue(f.exists())

			f_mod = self.tmp_dir / (mod_prefix + f.name)

			self.assertFalse(
				f_mod.exists(),
				f"{f_mod} should not exist before the test. Please delete.",
			)
			shutil.copyfile(f, f_mod)
			source_files.append(f_mod)
			with self.et:
				self.et.set_tags([f_mod], {"Caption-Abstract": d["Caption-Abstract"]})
				result = self.et.get_tags([f_mod], "IPTC:Caption-Abstract")[0]
				tag0 = list(result.values())[1]
			f_mod.unlink()
			self.assertEqual(tag0, d["Caption-Abstract"])

	# ---------------------------------------------------------------------------------------------------------
	def test_set_tags_file_existence(self):
		""" test setting tags on a non-existent file """
		check_value = self.et.check_execute  # save off current setting

		junk_tag = {"not_a_valid_tag_foo_bar": "lorem ipsum"}

		# set up temp working file
		mod_prefix = "test_"
		f = SCRIPT_PATH / "rose.jpg"
		f_mod = self.tmp_dir / (mod_prefix + f.name)
		self.assertTrue(f.exists())
		self.assertFalse(f_mod.exists())
		shutil.copyfile(f, f_mod)


		self.et.check_execute = False

		# no errors (aka exiftool fails silently, even though file doesn't exist)
		self.et.set_tags("foo.bar", junk_tag)

		# no errors (aka exiftool fails silently, even though it can't set this tag)
		self.et.set_tags(f_mod, junk_tag)



		self.et.check_execute = True

		# proper error handling, should raise error
		with self.assertRaises(ExifToolExecuteError):
			self.et.set_tags("foo.bar", junk_tag)


		# proper error handling, should also raise error
		with self.assertRaises(ExifToolExecuteError):
			self.et.set_tags(f_mod, junk_tag)


		self.et.check_execute = check_value


	# ---------------------------------------------------------------------------------------------------------
	def test_set_tags_files_invalid(self):
		""" test to cover the files == None """

		with self.assertRaises(ValueError):
			self.et.set_tags(None, [])

	# ---------------------------------------------------------------------------------------------------------
	def test_set_tags_tags_invalid(self):
		""" test to cover the files == None """

		with self.assertRaises(ValueError):
			self.et.set_tags("rose.jpg", None)


		with self.assertRaises(TypeError):
			self.et.set_tags("rose.jpg", object())

	# ---------------------------------------------------------------------------------------------------------


	def test_set_tags_list_keywords(self):
		"""
		test that covers setting keywords in set_tags() using a list (not using the ExifToolAlpha's keywords functionality directly)
		"""
		mod_prefix = "newkw_"
		expected_data = [{"SourceFile": "rose.jpg",
						  "Keywords": ["nature", "red plant", "flower"]}]
		source_files = []

		for d in expected_data:
			d["SourceFile"] = f = SCRIPT_PATH / d["SourceFile"]
			self.assertTrue(f.exists())
			f_mod = self.tmp_dir / (mod_prefix + f.name)
			self.assertFalse(
				f_mod.exists(),
				f"{f_mod} should not exist before the test. Please delete.",
			)

			shutil.copyfile(f, f_mod)
			source_files.append(f_mod)

			with self.et:
				self.et.set_tags(f_mod, {"Keywords": expected_data[0]["Keywords"]})
				ret_data = self.et.get_tags(f_mod, "IPTC:Keywords")

			f_mod.unlink()

			self.assertEqual(ret_data[0]["IPTC:Keywords"], expected_data[0]["Keywords"])

	# ---------------------------------------------------------------------------------------------------------



# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
