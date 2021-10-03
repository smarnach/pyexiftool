# -*- coding: utf-8 -*-
# PyExifTool <http://github.com/sylikc/pyexiftool>
# Copyright 2021 Kevin M (sylikc)

# More contributors in the CHANGELOG for the pull requests

# This file is part of PyExifTool.
#
# PyExifTool is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the licence, or
# (at your option) any later version, or the BSD licence.
#
# PyExifTool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING.GPL or COPYING.BSD for more details.

"""

This contains a helper class, which makes it easier to use the low-level ExifTool class

"""

import logging

from .exiftool import ExifTool

try:        # Py3k compatibility
	basestring
except NameError:
	basestring = (bytes, str)


from pathlib import PurePath  # Python 3.4 required

from typing import Any




# ======================================================================================================================


def _is_iterable(in_param: Any) -> bool:
	"""
	Checks if this item is iterable, instead of using isinstance(list), anything iterable can be ok

	NOTE: STRINGS ARE CONSIDERED ITERABLE by Python

	if you need to consider a code path for strings first, check that before checking if a parameter is iterable via this function
	"""
	# a different type of test of iterability, instead of using isinstance(list)
	# https://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
	try:
		iterator = iter(in_param)
	except TypeError:
		return False

	return True



# ======================================================================================================================

class ExifToolHelper(ExifTool):
	""" this class extends the low-level class with 'wrapper'/'helper' functionality
	It keeps low-level functionality with the base class but adds helper functions on top of it
	"""

	############################################################################################
	#################################### OVERLOADED METHODS ####################################
	############################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	def __init__(self, auto_start=True, **kwargs):
		"""
		auto_start = BOOLEAN.  will autostart the exiftool process on first command run

		all other parameters are passed directly to super-class' constructor: ExifTool(**)
		"""
		# call parent's constructor
		super().__init__(**kwargs)

		self._auto_start: bool = auto_start


	# ----------------------------------------------------------------------------------------------------------------------
	def execute(self, *params):
		""" overload the execute() method so that it checks if it's running first, and if not, start it """
		if self._auto_start and not self.running:
			self.run()

		return super().execute(*params)


	# ----------------------------------------------------------------------------------------------------------------------
	def terminate(self, **opts) -> None:
		""" overload the terminate() method so that if it's not running, won't execute (no warning will be output)

		options are passed directly to the parent verbatim
		"""
		if not self.running:
			return

		super().terminate(**opts)





	#####################################################################################
	#################################### NEW METHODS ####################################
	#####################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	def get_metadata(self, in_files, params=None):
		"""Return all meta-data for the given files.

			This will ALWAYS return a list

			in_files can be an iterable(strings) or a string.

			wildcard strings are accepted as it's passed straight to exiftool

		The return value will have the format described in the
		documentation of :py:meth:`get_tags()`.
		"""
		return self.get_tags(None, in_files, params=params)


	# ----------------------------------------------------------------------------------------------------------------------
	def get_tags(self, in_tags, in_files, params=None):
		"""Return only specified tags for the given files.

		The first argument is an iterable of tags.  The tag names may
		include group names, as usual in the format <group>:<tag>.

		If in_tags is None, or [], then returns all tags

		The second argument is an iterable of file names.  or a single file name

		The format of the return value is the same as for
		:py:meth:`execute_json()`.
		"""

		tags = None
		files = None

		if in_tags is None:
			# all tags
			tags = []
		elif isinstance(in_tags, basestring):
			tags = [in_tags]
		elif _is_iterable(in_tags):
			tags = in_tags
		else:
			raise TypeError("The argument 'in_tags' must be a str/bytes or a list")


		# TODO take Path-like objects in a list and single line convert with str()
		if isinstance(in_files, basestring):
			files = [in_files]
		elif isinstance(in_files, PurePath):
			# support for Path-like objects
			files = [str(in_files)]
		elif _is_iterable(in_files):
			files = in_files
		else:
			raise TypeError("The argument 'in_files' must be a str/bytes or a list")


		exec_params = []

		if params:
			# this is done to avoid accidentally modifying the reference object params
			exec_params.extend(params)

		# tags is always a list by this point.  It will always be iterable... don't have to check for None
		exec_params.extend(["-" + t for t in tags])

		exec_params.extend(files)

		ret = self.execute_json(*exec_params)

		if ret is None:
			raise RuntimeError("get_tags: exiftool returned no data")

		# TODO if last_status is <> 0, raise a warning that one or more files failed?

		return ret



	# ----------------------------------------------------------------------------------------------------------------------
