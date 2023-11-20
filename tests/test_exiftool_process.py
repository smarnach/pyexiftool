# -*- coding: utf-8 -*-
"""
Test :: ExifTool base class - process-related tests
"""

# standard
import unittest
import warnings

# custom
import exiftool
from exiftool.exceptions import ExifToolNotRunning


# bool which is set to True when running on Windows
# used below to workaround a Windows buggy interaction with exiftool subprocess
from exiftool.constants import PLATFORM_WINDOWS


class TestExifToolProcess(unittest.TestCase):


	# ---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifTool(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if hasattr(self, "et"):
			if self.et.running:
				self.et.terminate()
		if hasattr(self, "process"):
			if self.process.poll() is None:
				self.process.terminate()


	# ---------------------------------------------------------------------------------------------------------
	def test_termination_cm(self):
		# Test correct subprocess start and termination when using
		# self.et as a context manager
		self.assertFalse(self.et.running)
		self.assertRaises(ExifToolNotRunning, self.et.execute)
		with self.et:
			self.assertTrue(self.et.running)
			with warnings.catch_warnings(record=True) as w:
				self.et.run()
				self.assertEqual(len(w), 1)
				self.assertTrue(issubclass(w[0].category, UserWarning))
			self.process = self.et._process
			self.assertEqual(self.process.poll(), None)
		self.assertFalse(self.et.running)
		self.assertNotEqual(self.process.poll(), None)


	# ---------------------------------------------------------------------------------------------------------
	def test_termination_explicit(self):
		# Test correct subprocess start and termination when
		# explicitly using start() and terminate()
		self.et.run()
		self.process = self.et._process
		self.assertEqual(self.process.poll(), None)
		self.et.terminate()
		self.assertNotEqual(self.process.poll(), None)

		# terminate when not running
		with warnings.catch_warnings(record=True) as w:
			self.et.terminate()
			self.assertEqual(len(w), 1)
			self.assertTrue(issubclass(w[0].category, UserWarning))


	# ---------------------------------------------------------------------------------------------------------
	def test_process_died_running_status(self):
		""" Test correct .running status if process dies by itself """

		# There is a very weird bug triggered on WINDOWS only which I've described here: https://exiftool.org/forum/index.php?topic=12472.0
		# it happens specifically when you forcefully kill the process, but at least one command has run since launching, the exiftool wrapper on windows does not terminate the child process
		# it's a very strange interaction and causes a zombie process to remain, and python hangs
		#
		# either kill the tree with psutil, or do it this way...

		# WINDOWS WORKAROUND: take out the method that is called on load (probably not the way to do this well... you can take out this line and watch Python interpreter hang at .kill() below
		if PLATFORM_WINDOWS:
			self.et._parse_ver = lambda: None


		self.et.run()
		self.process = self.et._process
		self.assertTrue(self.et.running)

		# kill the process, out of ExifTool's control
		self.process.kill()
		# TODO freeze here on windows if there is a zombie process b/c killing immediate exiftool does not kill the spawned subprocess
		outs, errs = self.process.communicate()

		with warnings.catch_warnings(record=True) as w:
			self.assertFalse(self.et.running)
			self.assertEqual(len(w), 1)
			self.assertTrue(issubclass(w[0].category, UserWarning))

		# after removing that function, delete the object so it gets recreated cleanly
		del self.et


	# ---------------------------------------------------------------------------------------------------------
	def test_termination_implicit(self):
		# Test implicit process termination on garbage collection

		# WINDOWS WORKAROUND: take out the method that is called on load (see test_process_died_running_status())
		if PLATFORM_WINDOWS:
			self.et._parse_ver = lambda: None

		self.et.run()
		self.process = self.et._process
		# TODO freze here on windows for same reason as in test_process_died_running_status() as a zombie process remains
		del self.et
		self.assertNotEqual(self.process.poll(), None)


# ---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
