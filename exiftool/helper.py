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


#from pathlib import PurePath  # Python 3.4 required

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

	##########################################################################################
	#################################### OVERRIDE METHODS ####################################
	##########################################################################################

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
		""" override the execute() method so that it checks if it's running first, and if not, start it """
		if self._auto_start and not self.running:
			self.run()

		return super().execute(*params)


	# ----------------------------------------------------------------------------------------------------------------------
	def run(self) -> None:
		""" override the run() method so that if it's running, won't call super() method (so no warning about 'ExifTool already running' will trigger) """
		if self.running:
			return

		super().run()


	# ----------------------------------------------------------------------------------------------------------------------
	def terminate(self, **opts) -> None:
		""" override the terminate() method so that if it's not running, won't call super() method (so no warning about 'ExifTool not running' will trigger)

		options are passed directly to the parent verbatim
		"""
		if not self.running:
			return

		super().terminate(**opts)





	#####################################################################################
	#################################### NEW METHODS ####################################
	#####################################################################################


	# all generic helper functions will follow a convention of
	# function(files to be worked on, ... , params=)


	# ----------------------------------------------------------------------------------------------------------------------
	def get_metadata(self, files, params=None):
		"""Return all meta-data for the given files.

			This will returns a list, or None

			files parameter matches :py:meth:`get_tags()`

			wildcard strings are accepted as it's passed straight to exiftool

		The return value will have the format described in the
		documentation of :py:meth:`get_tags()`.
		"""
		return self.get_tags(files, None, params=params)


	# ----------------------------------------------------------------------------------------------------------------------
	def get_tags(self, files, tags, params=None):
		"""Return only specified tags for the given files.

		The first argument is the files to be worked on.  It can be:
		* an iterable of strings/bytes
		* string/bytes

		The list is copied and any non-basestring elements are converted to str (to support PurePath and other similar objects)

		Filenames are NOT checked for existence, that is left up to the caller.
		It is passed directly to exiftool, which supports wildcards, etc.  Please refer to the exiftool documentation


		The second argument is an iterable of tags.  The tag names may
		include group names, as usual in the format <group>:<tag>.

		If tags is None, or [], then returns all tags


		The format of the return value is the same as for
		:py:meth:`execute_json()`.
		"""

		final_tags = None
		final_files = None

		if tags is None:
			# all tags
			final_tags = []
		elif isinstance(tags, basestring):
			final_tags = [tags]
		elif _is_iterable(tags):
			final_tags = tags
		else:
			raise TypeError(f"{self.__class__.__name__}.get_tags: argument 'tags' must be a str/bytes or a list")

		if not files:
			# Exiftool process would return None anyways
			raise ValueError(f"{self.__class__.__name__}.get_tags: argument 'files' cannot be empty")
		elif isinstance(files, basestring):
			final_files = [files]
		elif not _is_iterable(files):
			final_files = [str(files)]
		else:
			# duck-type any iterable given, and str() it
			# this was originally to support Path() but it's now generic to support any object that str() to something useful

			# Thanks @jangop for the single line contribution!
			final_files = [x if isinstance(x, basestring) else str(x) for x in files]

			# TODO: this list copy could be expensive if the input is a very huge list.  Perhaps in the future have a flag that takes the lists in verbatim without any processing?

		exec_params = []

		if params:
			if isinstance(params, basestring):
				# if params is a string, append it as is
				exec_params.append(params)
			elif _is_iterable(params):
				# this is done to avoid accidentally modifying the reference object params
				exec_params.extend(params)
			else:
				raise TypeError(f"{self.__class__.__name__}.get_tags: argument 'params' must be a str or a list")

		# tags is always a list by this point.  It will always be iterable... don't have to check for None
		exec_params.extend([f"-{t}" for t in final_tags])

		exec_params.extend(final_files)

		try:
			ret = self.execute_json(*exec_params)
		except OutputEmpty:
			raise
			#raise RuntimeError(f"{self.__class__.__name__}.get_tags: exiftool returned no data")
		except OutputNotJSON:
			# TODO if last_status is <> 0, raise a warning that one or more files failed?
			raise

		return ret



	# ----------------------------------------------------------------------------------------------------------------------
