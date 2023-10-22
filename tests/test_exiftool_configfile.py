"""
Test :: ExifTool base class - config_file attribute
"""
# standard
import unittest

# test helpers
from tests.common_util import et_get_temp_dir

# custom
import exiftool
from exiftool.exceptions import ExifToolRunning




class TestExifToolConfigFile(unittest.TestCase):

	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifTool(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if self.et.running:
			self.et.terminate()

	# ---------------------------------------------------------------------------------------------------------

	def test_configfile_attribute(self):
		current = self.et.config_file

		with self.assertRaises(FileNotFoundError):
			self.et.config_file = "foo.bar"

		# see if Python 3.9.5 fixed this ... raises OSError right now and is a pathlib glitch https://bugs.python.org/issue35306
		#self.et.config_file = "\"C:\\\"\"C:\\"

		# then restore current config_file
		self.et.config_file = current

		self.assertFalse(self.et.running)
		self.et.run()
		self.assertTrue(self.et.running)

		with self.assertRaises(ExifToolRunning):
			self.et.config_file = None

		self.et.terminate()

	# ---------------------------------------------------------------------------------------------------------
	def test_configfile_set(self):
		(temp_obj, temp_dir) = et_get_temp_dir(suffix="config")

		# set config file to empty, which is valid (should not throw error)
		self.et.config_file = ""

		# create a config file, and set it and test that it works
		# a file that returns 1 is valid as a config file
		tmp_config_file = temp_dir / "config_test.txt"
		with open(tmp_config_file, 'w') as f:
			f.write("1;\n")

		self.et.config_file = tmp_config_file

		self.et.run()
		self.assertTrue(self.et.running)

		self.et.terminate()



# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
