# -*- coding: utf-8 -*-
#
# This file is part of PyExifTool.
#
# PyExifTool <http://github.com/sylikc/pyexiftool>
#
# Copyright 2019-2022 Kevin M (sylikc)
# Copyright 2012-2014 Sven Marnach
#
# Community contributors are listed in the CHANGELOG.md for the PRs
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
This submodule contains the ``ExifToolHelper`` class, which makes the core ``ExifTool`` class easier, and safer to use.

.. note::
	:py:class:`exiftool.helper.ExifToolHelper` class of this submodule is available in the ``exiftool`` namespace as :py:class:`exiftool.ExifToolHelper`

"""

import re
import logging

from .exiftool import ExifTool
from .exceptions import ExifToolOutputEmptyError, ExifToolJSONInvalidError, ExifToolExecuteError, ExifToolTagNameError

try:        # Py3k compatibility
	basestring
except NameError:
	basestring = (bytes, str)


#from pathlib import PurePath  # Python 3.4 required

from typing import Any, Union, Optional, List, Dict




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
	"""
	This class extends the low-level :py:class:`exiftool.ExifTool` class with 'wrapper'/'helper' functionality

	It keeps low-level core functionality with the base class but extends helper functions in a separate class
	"""

	##########################################################################################
	#################################### OVERRIDE METHODS ####################################
	##########################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	def __init__(self, auto_start: bool = True, check_execute: bool = True, check_tag_names: bool = True, **kwargs) -> None:
		"""
		:param bool auto_start: Will automatically start the exiftool process on first command run, defaults to True
		:param bool check_execute: Will check the exit status (return code) of all commands.  This catches some invalid commands passed to exiftool subprocess, defaults to True.  See :py:attr:`check_execute` for more info.
		:param bool check_tag_names: Will check the tag names provided to methods which work directly with tag names.  This catches unintended uses and bugs, default to True.  See :py:attr:`check_tag_names` for more info.

		:param kwargs: All other parameters are passed directly to the super-class constructor: :py:meth:`exiftool.ExifTool.__init__()`
		"""
		# call parent's constructor
		super().__init__(**kwargs)

		self._auto_start: bool = auto_start
		self._check_execute: bool = check_execute
		self._check_tag_names: bool = check_tag_names


	# ----------------------------------------------------------------------------------------------------------------------
	def execute(self, *params) -> str:
		"""
		Override the :py:meth:`exiftool.ExifTool.execute()` method

		Adds logic to auto-start if not running, if :py:attr:`auto_start` == True

		:raises ExifToolExecuteError: If :py:attr:`check_execute` == True, and exit status was non-zero
		"""
		if self._auto_start and not self.running:
			self.run()

		result: str = super().execute(*params)

		# imitate the subprocess.run() signature.  check=True will check non-zero exit status
		if self._check_execute and self._last_status:
			raise ExifToolExecuteError(self._last_status, self._last_stdout, self._last_stderr, params)

		return result

	# ----------------------------------------------------------------------------------------------------------------------
	def run(self) -> None:
		"""
		override the :py:meth:`exiftool.ExifTool.run()` method

		Adds logic to check if already running.  Will not attempt to run if already running (so no warning about 'ExifTool already running' will trigger) """
		if self.running:
			return

		super().run()


	# ----------------------------------------------------------------------------------------------------------------------
	def terminate(self, **opts) -> None:
		"""
		override the :py:meth:`exiftool.ExifTool.terminate()` method

		Adds logic to check if not running (so no warning about 'ExifTool not running' will trigger)

		opts are passed directly to the parent verbatim
		"""
		if not self.running:
			return

		super().terminate(**opts)


	########################################################################################
	#################################### NEW PROPERTIES ####################################
	########################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def auto_start(self) -> bool:
		"""
		Read-only property.  Gets the current setting passed into the constructor as to whether auto_start is enabled or not.

		(There's really no point to having this a read-write property, but allowing a read can be helpful at runtime to detect expected behavior.)
		"""
		return self._auto_start



	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def check_execute(self) -> bool:
		"""
		Flag to enable/disable checking exit status (return code) on execute

		If enabled, will raise :py:exc:`exiftool.exceptions.ExifToolExecuteError` if a non-zero exit status is returned during :py:meth:`execute()`

		.. warning::
			While this property is provided to give callers an option to enable/disable error checking, it is generally **NOT** recommended to disable ``check_execute``.

			**If disabled, exiftool will fail silently, and hard-to-catch bugs may arise.**

			That said, there may be some use cases where continue-on-error behavior is desired.  (Example: dump all exif in a directory with files which don't all have the same tags, exiftool returns exit code 1 for unknown files, but results are valid for other files with those tags)

		:getter: Returns current setting
		:setter: Enable or Disable the check

			.. note::
				This settings can be changed any time and will only affect subsequent calls

		:type: bool
		"""
		return self._check_execute

	@check_execute.setter
	def check_execute(self, new_setting: bool) -> None:
		self._check_execute = new_setting


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def check_tag_names(self) -> bool:
		"""
		Flag to enable/disable checking of tag names

		If enabled, will raise :py:exc:`exiftool.exceptions.ExifToolTagNameError` if an invalid tag name is detected.

		.. warning::
			ExifToolHelper only checks the validity of the Tag **NAME** based on a simple regex pattern.

			* It *does not* validate whether the tag name is actually valid on the file type(s) you're accessing.
			* It *does not* validate whether the tag you passed in that "looks like" a tag is actually an option
			* It does support a "#" at the end of the tag name to disable print conversion

			Please refer to `ExifTool Tag Names`_ documentation for a complete list of valid tags recognized by ExifTool.

		.. warning::
			While this property is provided to give callers an option to enable/disable tag names checking, it is generally **NOT** recommended to disable ``check_tag_names``.

			**If disabled, you could accidentally edit a file when you meant to read it.**

			Example: ``get_tags("a.jpg", "tag=value")`` will call ``execute_json("-tag=value", "a.jpg")`` which will inadvertently write to a.jpg instead of reading it!

			That said, if PH's exiftool changes its tag name regex and tag names are being erroneously rejected because of this flag, disabling this could be used as a workaround (more importantly, if this is happening, please `file an issue`_!).

		:getter: Returns current setting
		:setter: Enable or Disable the check

			.. note::
				This settings can be changed any time and will only affect subsequent calls

		:type: bool


		.. _file an issue: https://github.com/sylikc/pyexiftool/issues
		.. _ExifTool Tag Names: https://exiftool.org/TagNames/
		"""
		return self._check_tag_names

	@check_tag_names.setter
	def check_tag_names(self, new_setting: bool) -> None:
		self._check_tag_names = new_setting




	# ----------------------------------------------------------------------------------------------------------------------






	#####################################################################################
	#################################### NEW METHODS ####################################
	#####################################################################################


	# all generic helper functions will follow a convention of
	# function(files to be worked on, ... , params=)


	# ----------------------------------------------------------------------------------------------------------------------
	def get_metadata(self, files: Union[str, List], params: Optional[Union[str, List]] = None) -> List:
		"""
		Return all metadata for the given files.

		:param files: Files parameter matches :py:meth:`get_tags()`

		:param params: Optional parameters to send to *exiftool*
		:type params: list or None

		:return: The return value will have the format described in the documentation of :py:meth:`get_tags()`.
		"""
		return self.get_tags(files, None, params=params)


	# ----------------------------------------------------------------------------------------------------------------------
	def get_tags(self, files: Union[str, List], tags: Optional[Union[str, List]], params: Optional[Union[str, List]] = None) -> List:
		"""
		Return only specified tags for the given files.

		:param files: File(s) to be worked on.

			* If a ``str`` is provided, it will get tags for a single file
			* If an iterable is provided, the list is copied and any non-basestring elements are converted to str (to support ``PurePath`` and other similar objects)

			.. warning::
				Currently, filenames are NOT checked for existence!  That is left up to the caller.

			.. warning::
				Wildcard strings are valid and passed verbatim to exiftool.

				However, exiftool's wildcard matching/globbing may be different than Python's matching/globbing, which may cause unexpected behavior if you're using one and comparing the result to the other.  Read `ExifTool Common Mistakes - Over-use of Wildcards in File Names`_ for some related info.

		:type files: str or list


		:param tags: Tag(s) to read.  If tags is None, or [], method will returns all tags

			.. note::
				The tag names may include group names, as usual in the format ``<group>:<tag>``.

		:type tags: str, list, or None


		:param params: Optional parameter(s) to send to *exiftool*
		:type params: str, list, or None


		:return: The format of the return value is the same as for :py:meth:`exiftool.ExifTool.execute_json()`.


		:raises ValueError: Invalid Parameter
		:raises TypeError: Invalid Parameter
		:raises ExifToolExecuteError: If :py:attr:`check_execute` == True, and exit status was non-zero


		.. _ExifTool Common Mistakes - Over-use of Wildcards in File Names: https://exiftool.org/mistakes.html#M2

		"""

		final_tags:  Optional[List] = None
		final_files: List = self.__class__._parse_arg_files(files)

		if tags is None:
			# all tags
			final_tags = []
		elif isinstance(tags, basestring):
			final_tags = [tags]
		elif _is_iterable(tags):
			final_tags = tags
		else:
			raise TypeError(f"{self.__class__.__name__}.get_tags: argument 'tags' must be a str/bytes or a list")

		if self._check_tag_names:
			# run check if enabled
			self.__class__._check_tag_list(final_tags)

		exec_params: List = []

		self.__class__._extend_arg_params(exec_params, params)

		# tags is always a list by this point.  It will always be iterable... don't have to check for None
		exec_params.extend([f"-{t}" for t in final_tags])

		exec_params.extend(final_files)

		try:
			ret = self.execute_json(*exec_params)
		except ExifToolOutputEmptyError:
			raise
			#raise RuntimeError(f"{self.__class__.__name__}.get_tags: exiftool returned no data")
		except ExifToolJSONInvalidError:
			raise
		except ExifToolExecuteError:
			# if last_status is <> 0, raise an error that one or more files failed?
			raise

		return ret


	# ----------------------------------------------------------------------------------------------------------------------
	def set_tags(self, files: Union[str, List], tags: Dict, params: Optional[Union[str, List]] = None):
		"""
		Writes the values of the specified tags for the given file(s).

		:param files: File(s) to be worked on.

			* If a ``str`` is provided, it will set tags for a single file
			* If an iterable is provided, the list is copied and any non-basestring elements are converted to str (to support ``PurePath`` and other similar objects)

			.. warning::
				Currently, filenames are NOT checked for existence!  That is left up to the caller.

			.. warning::
				Wildcard strings are valid and passed verbatim to exiftool.

				However, exiftool's wildcard matching/globbing may be different than Python's matching/globbing, which may cause unexpected behavior if you're using one and comparing the result to the other.  Read `ExifTool Common Mistakes - Over-use of Wildcards in File Names`_ for some related info.

		:type files: str or list


		:param tags: Tag(s) to write.

			Dictionary keys = tags, values = tag values (str or list)

			* If a value is a str, will set key=value
			* If a value is a list, will iterate over list and set each individual value to the same tag (

			.. note::
				The tag names may include group names, as usual in the format ``<group>:<tag>``.

			.. note::
				Value of the dict can be a list, in which case, the tag will be passed with each item in the list, in the order given

				This allows setting things like ``-Keywords=a -Keywords=b -Keywords=c`` by passing in ``tags={"Keywords": ['a', 'b', 'c']}``

		:type tags: dict


		:param params: Optional parameter(s) to send to *exiftool*
		:type params: str, list, or None


		:return: The format of the return value is the same as for :py:meth:`execute()`.


		:raises ValueError: Invalid Parameter
		:raises TypeError: Invalid Parameter
		:raises ExifToolExecuteError: If :py:attr:`check_execute` == True, and exit status was non-zero


		.. _ExifTool Common Mistakes - Over-use of Wildcards in File Names: https://exiftool.org/mistakes.html#M2

		"""
		final_files: List = self.__class__._parse_arg_files(files)

		if not tags:
			raise ValueError(f"{self.__class__.__name__}.set_tags: argument 'tags' cannot be empty")
		elif not isinstance(tags, dict):
			raise TypeError(f"{self.__class__.__name__}.set_tags: argument 'tags' must be a dict")


		if self._check_tag_names:
			# run check if enabled
			self.__class__._check_tag_list(list(tags))  # gets only the keys (tag names)

		exec_params: List = []

		self.__class__._extend_arg_params(exec_params, params)

		for tag, value in tags.items():
			# contributed by @daviddorme in https://github.com/sylikc/pyexiftool/issues/12#issuecomment-821879234
			# allows setting things like Keywords which require separate directives
			# > exiftool -Keywords=keyword1 -Keywords=keyword2 -Keywords=keyword3 file.jpg
			# which are not supported as duplicate keys in a dictionary
			if isinstance(value, list):
				for item in value:
					exec_params.append(f"-{tag}={item}")
			else:
				exec_params.append(f"-{tag}={value}")

		exec_params.extend(final_files)

		try:
			return self.execute(*exec_params)
			#TODO if execute returns data, then error?
		except ExifToolExecuteError:
			# last status non-zero
			raise


	# ----------------------------------------------------------------------------------------------------------------------







	#########################################################################################
	#################################### PRIVATE METHODS ####################################
	#########################################################################################



	# ----------------------------------------------------------------------------------------------------------------------
	@staticmethod
	def _parse_arg_files(files: Union[str, List]) -> List:
		"""
		This logic to process the files argument is common across most ExifToolHelper methods

		It can be used by a developer to process the files argument the same way if this class is extended

		:param files: File(s) to be worked on.
		:type files: str or list

		:return: A list of one or more elements containing strings of files

		:raises ValueError: Files parameter is empty
		"""

		final_files: List = []

		if not files:
			# Exiftool process would return an error anyways
			raise ValueError(f"ERROR: Argument 'files' cannot be empty")
		elif isinstance(files, basestring):
			# if it's a string
			final_files = [files]
		elif not _is_iterable(files):
			# if it's not a string but also not iterable
			final_files = [str(files)]
		else:
			# duck-type any iterable given, and str() it

			# this was originally to support Path() but it's now generic enough to support any object that str() to something useful

			# Thanks @jangop for the single line contribution!
			final_files = [x if isinstance(x, basestring) else str(x) for x in files]

			# TODO: this list copy could be expensive if the input is a very huge list.  Perhaps in the future have a flag that takes the lists in verbatim without any processing?

		return final_files


	# ----------------------------------------------------------------------------------------------------------------------
	@staticmethod
	def _extend_arg_params(mod_list: List, params: Optional[Union[str, List]]) -> None:
		"""
		This protected method is a helper method to extend a list if params is given

		:param list mod_list: List to modify

		:param params: Extra params to append to mod_list, if provided
		:type params: str, list, or None

		:raises TypeError: params is specified but not a str or a list
		"""
		if params:
			if isinstance(params, basestring):
				# if params is a string, append it as is
				mod_list.append(params)
			elif _is_iterable(params):
				# we extend an empty list to avoid accidentally modifying the reference object params
				mod_list.extend(params)
			else:
				raise TypeError(f"Argument 'params' must be a str or a list")  # or None, but no need to be explicit if specified



	# ----------------------------------------------------------------------------------------------------------------------
	@staticmethod
	def _check_tag_list(tags: List) -> None:
		"""
		Private method.  This method is used to check the validity of a tag list passed in.

		See any notes/warnings in the property :py:attr:`check_tag_names` to get a better understanding of what this is for and not for.

		:param list tags: List of tags to check

		:return: None if checks passed.  Raises an error otherwise.  (Think of it like an assert statement)
		"""
		# In the future if a specific version changed the match pattern,
		# we can check self.version ... then this method will no longer
		# be static and requires the underlying exiftool process to be running to get the self.version
		#
		# This is not done right now because the odds of the tag name format changing is very low, and requirin
		# exiftool to be running during this tag check could introduce unneccesary overhead at this time



		# According to the exiftool source code, the valid regex on tags is (/^([-\w*]+:)*([-\w*?]+)#?$/)
		# However, it appears that "-" may be allowed within a tag name/group (i.e. https://exiftool.org/TagNames/XMP.html Description tags)
		#
		# \w in Perl => https://perldoc.perl.org/perlrecharclass#Backslash-sequences
		# \w in Python => https://docs.python.org/3/library/re.html#regular-expression-syntax
		#
		# Perl vs Python's "\w" seem to mean slightly different things, so we write our own regex / matching algo


		# * make sure the first character is not a special one
		# * "#" can only appear at the end
		# * Tag:Tag:tag is not valid, but passes the simple regex (it's ok, this is not supposed to be a catch-all)... exiftool subprocess accepts it anyways, even if invalid.
		# * *wildcard* tags are permitted by exiftool
		tag_regex = r"[\w\*][\w\:\-\*]*(#|)"

		for t in tags:
			if re.fullmatch(tag_regex, t) is None:
				raise ExifToolTagNameError(t)

		# returns nothing, if no error was raised, the tags passed

		# considering making this...
		# * can't begin with -
		# * can't have "=" anywhere, and that's it...
		# there's a lot of variations which might make this code buggy for some edge use cases



	# ----------------------------------------------------------------------------------------------------------------------

