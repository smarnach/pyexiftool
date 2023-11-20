# -*- coding: utf-8 -*-
"""
Test :: ExifToolHelper - numeric tags tests
"""

# standard
import unittest
import shutil
import json
from decimal import Decimal

# test helpers
from tests.common_util import et_get_temp_dir, TEST_IMAGE_DIR, TEST_IMAGE_JPG

# custom
import exiftool

# test well known alternative JSON processors
try:
	import ujson
	has_ujson = True
except ImportError:
	has_ujson = False

try:
	import simplejson
	has_simplejson = True
except ImportError:
	has_simplejson = False

try:
	import orjson
	has_orjson = True
except ImportError:
	has_orjson = False

# TODO rapidjson, but I think the result will be the same


class TestHelperFloatTags(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifToolHelper(
			common_args=["-n", "-overwrite_original"],
			encoding="UTF-8"
		)

		# set up the file to write tags to to test
		# for this test, we write to the same file
		(self.temp_obj, self.temp_dir) = et_get_temp_dir(suffix="tagcommentnum")

		self.jpg_file = self.temp_dir / ("tagnum_" + TEST_IMAGE_JPG.name)

		shutil.copyfile(TEST_IMAGE_JPG, self.jpg_file)

		# all tests use the same test for this comment number thing
		self.test_data_str = [
			{"Comment": 1},
			{"Comment": -1},
			{"Comment": 1.1},
			{"Comment": -1.1},

			{"Comment": "10"},
			{"Comment": "-10"},
			{"Comment": "1.10"},
			{"Comment": "-1.10"},
			{"Comment": "0.1000"},
			{"Comment": "1.33700e+40"},

			{"Comment": "1       "},
			#{"Comment": " -1"},  #possible exiftool bug, see blow on test cases

			[{"Comment": Decimal('935733.817019799357333475932629142801644788893573383506621454627967')}, '935733.817019799357333475932629142801644788893573383506621454627967'],
			[{"Comment": Decimal('935733.81701979935')}, '935733.81701979935'],

			# numbers are as is
			[{"FocalLength": "00.1000"}, 0.1],
			[{"FocalLength": "010"}, 10],
			[{"FocalLength": "01.0"}, 1],
		]


	def tearDown(self):
		self.et.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def check_testdata(self, test_data, compare_str=False):
		"""
		check test_data in a specific format specified below

		this routine allows us to check numerous cases in different configurations
		"""

		with self.et:
			for d in test_data:
				"""
				format of test_data is a LIST of either:
					DICT = {"tag": <value to set, and compare>}
					LIST = [{"tag": <value to set>}, value to check]

				only one tag to set, this is all just for testing
				"""
				set_tag_dict = None
				check_tag_value = None
				set_tag_key = None

				if isinstance(d, dict):
					set_tag_dict = d

					# unpack into key/value
					# https://stackoverflow.com/questions/58129118/how-to-unpack-dict-with-one-key-value-pair-to-two-variables-more-elegantly
					set_tag_key, check_tag_value = next(iter(set_tag_dict.items()))
				else:
					set_tag_dict = d[0]
					check_tag_value = d[1]

					# unpack into key/value, ignore value
					set_tag_key = next(iter(set_tag_dict.items()))[0]

				# set the data
				self.et.set_tags(self.jpg_file, set_tag_dict)

				# get the data
				r = self.et.get_tags(self.jpg_file, set_tag_key)
				#print(r)

				# check
				if compare_str:
					# if compare by str only, a shorthand for the tests which will return str
					self.assertEqual(str(r[0][set_tag_key]), str(check_tag_value))
				else:
					self.assertEqual(r[0][set_tag_key], check_tag_value)


	# ---------------------------------------------------------------------------------------------------------
	def test_baseline_exiftool_behavior(self):
		"""
		test baseline exiftool behavior

		If this test has failed, it means that exiftool returned output that has changed behavior since
		this test was written.  You should investigate what changed before trying to fix any other tests
		"""

		# set default
		self.et.set_json_loads(json.loads)



		test_data = [
			# baseline tests, exiftool returns a str in json

			## notice how the default exiftool behavior is different depending on field type

			# Comment is a string field
			# FocalLength is a float field

			{"Comment": "01"},
			{"Comment": "0000001"},
			{"Comment": "00.1"},
			{"Comment": "00.1000"},
			{"Comment": "NaN"},
			{"Comment": "Infinity"},
			{"Comment": "-Infinity"},
			{"Comment": "nan"},
			{"Comment": "inf"},
			[{"Comment": Decimal('935733.817019799357333475932629142801644788893573383506621454627967')}, '935733.817019799357333475932629142801644788893573383506621454627967'],
			[{"Comment": "   1      "}, "  1      "],  # exiftool removes a space (might be an exiftool bug)  TODO more investigation on this specific case, and report bug if it is
			[{"Comment": "    -1"}, "   -1"],  # exiftool removes a leading space
			{"Comment": "1      "},

			[{"FocalLength": "00.1000"}, 0.1],
			[{"FocalLength": "010"}, 10],
			[{"FocalLength": "01.0"}, 1],
			[{"FocalLength": "blahblahblah"}, 1],  # this is ignored by exiftool, so it uses previous set value

			# exiftool returns a number here (text field)
			[{"Comment": " 1"}, 1],
			[{"Comment": " -1"}, -1],
			{"Comment": 1},
			{"Comment": -1},
			{"Comment": 1.1},
			{"Comment": -1.1},

			[{"Comment": "10"}, 10],
			[{"Comment": "-10"}, -10],
			[{"Comment": "1.10"}, 1.1],
			[{"Comment": "-1.10"}, -1.1],
			[{"Comment": "0.1000"}, 0.1],
			[{"Comment": "1.337e+40"}, 1.337e+40],
			[{"Comment": "1.33700e+40"}, 1.337e+40],

			[{"Comment": Decimal('935733.81701979935')}, 935733.8170197994],  # notice that exiftool rounds here

		]

		self.check_testdata(test_data)


	# ---------------------------------------------------------------------------------------------------------
	def test_json_tag_comment_number(self):
		"""
		test that covers a numeric tag causing data mismatch

		with the parameters to get it to pass (default json processor)

		Addresses: https://github.com/sylikc/pyexiftool/issues/76
		"""

		self.et.set_json_loads(json.loads, parse_float=str)

		# should return all strings
		self.check_testdata(self.test_data_str, compare_str=True)


	# ---------------------------------------------------------------------------------------------------------
	@unittest.skipIf(has_simplejson is False, "simplejson not installed")
	def test_simplejson_tag_comment_number(self):
		"""
		test that covers a numeric tag causing data mismatch

		simplejson is the CPython json implementation in pure python (slower)
		"""

		self.et.set_json_loads(simplejson.loads, parse_float=str)

		self.check_testdata(self.test_data_str, compare_str=True)


	# ---------------------------------------------------------------------------------------------------------
	@unittest.skipIf(has_ujson is False, "ujson not installed")
	@unittest.expectedFailure
	def test_ujson_tag_comment_number(self):
		"""
		test that covers a numeric tag causing data mismatch

		ujson does not support the parse_float, and it's an outstanding bug
			https://github.com/ultrajson/ultrajson/issues/401
			https://github.com/ultrajson/ultrajson/issues/600
		"""

		self.et.set_json_loads(ujson.loads)

		#ujson.loads('{"test": 1}', parse_float=str)

		self.check_testdata(self.test_data_str, compare_str=True)


	# ---------------------------------------------------------------------------------------------------------
	@unittest.skipIf(has_orjson is False, "orjson not installed")
	@unittest.expectedFailure
	def test_orjson_tag_comment_number(self):
		"""
		test that covers a numeric tag causing data mismatch

		orjson does not support this type of processing
			https://github.com/ijl/orjson/issues/21
		"""

		self.et.set_json_loads(orjson.loads)

		self.check_testdata(self.test_data_str, compare_str=True)


	# ---------------------------------------------------------------------------------------------------------
	def test_json_loads_invalid(self):
		"""
		tests that an invalid set is caught (coverage test)
		"""
		with self.assertRaises(TypeError):
			self.et.set_json_loads("hi")


# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
