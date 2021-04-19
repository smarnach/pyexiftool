# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import exiftool
import warnings
#import os
#import shutil
#import sys

class TestExifTool(unittest.TestCase):

	#---------------------------------------------------------------------------------------------------------
	def setUp(self):
		self.et = exiftool.ExifTool(common_args=["-G", "-n", "-overwrite_original"])

	def tearDown(self):
		if hasattr(self, "et"):
			if self.et.running:
				self.et.terminate()
		if hasattr(self, "process"):
			if self.process.poll() is None:
				self.process.terminate()
	#---------------------------------------------------------------------------------------------------------
	def test_running_attribute(self):
		# test if we can read "running" but can't set it
		self.assertFalse(self.et.running)
		with self.assertRaises(AttributeError):
			self.et.running = True
	#---------------------------------------------------------------------------------------------------------
	def test_executable_attribute(self):
		# test if we can read "running" but can't set it
		self.assertFalse(self.et.running)
		self.et.run()
		self.assertTrue(self.et.running)
		with self.assertRaises(RuntimeError):
			self.et.executable = "x"
		self.et.terminate()
		with self.assertRaises(FileNotFoundError):
			self.et.executable = "lkajsdfoleiawjfasv"
		self.assertFalse(self.et.running)
	#---------------------------------------------------------------------------------------------------------
	def test_blocksize_attribute(self):
		current = self.et.block_size

		# arbitrary
		self.et.block_size = 4
		self.assertEqual(self.et.block_size, 4)

		with self.assertRaises(ValueError):
			self.et.block_size = -1

		# restore
		self.et.block_size = current

	#---------------------------------------------------------------------------------------------------------
	
	def test_configfile_attribute(self):
		current = self.et.config_file
		
		
		# TODO create a config file, and set it and test that it works
		
		self.assertFalse(self.et.running)
		self.et.run()
		self.assertTrue(self.et.running)
		
		with self.assertRaises(RuntimeError):
			self.et.config_file = None
		
		self.et.terminate()
		
	
	#---------------------------------------------------------------------------------------------------------
	def test_termination_cm(self):
		# Test correct subprocess start and termination when using
		# self.et as a context manager
		self.assertFalse(self.et.running)
		self.assertRaises(RuntimeError, self.et.execute)
		with self.et:
			self.assertTrue(self.et.running)
			with warnings.catch_warnings(record=True) as w:
				self.et.run()
				self.assertEquals(len(w), 1)
				self.assertTrue(issubclass(w[0].category, UserWarning))
			self.process = self.et._process
			self.assertEqual(self.process.poll(), None)
		self.assertFalse(self.et.running)
		self.assertNotEqual(self.process.poll(), None)
	#---------------------------------------------------------------------------------------------------------
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
			self.assertEquals(len(w), 1)
			self.assertTrue(issubclass(w[0].category, UserWarning))

	#---------------------------------------------------------------------------------------------------------
	def test_termination_implicit(self):
		# Test implicit process termination on garbage collection
		self.et.run()
		self.process = self.et._process
		del self.et
		self.assertNotEqual(self.process.poll(), None)
	#---------------------------------------------------------------------------------------------------------
	def test_process_died_running_status(self):
		# Test correct .running status if process dies by itself
		self.et.run()
		self.process = self.et._process
		self.assertTrue(self.et.running)
		# kill the process, out of ExifTool's control
		self.process.kill()
		outs, errs = self.process.communicate()

		with warnings.catch_warnings(record=True) as w:
			self.assertFalse(self.et.running)
			self.assertEquals(len(w), 1)
			self.assertTrue(issubclass(w[0].category, UserWarning))
	#---------------------------------------------------------------------------------------------------------
	def test_invalid_args_list(self):
		# test to make sure passing in an invalid args list will cause it to error out
		with self.assertRaises(TypeError):
			exiftool.ExifTool(common_args="not a list")


#---------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()
