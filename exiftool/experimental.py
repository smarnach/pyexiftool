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

This contains the "experimental" functionality.  In the grand scheme of things, this class
contains "untested" functionality, or those that are less used, and may merge in with the
ExifToolHelper() class at some point.

The starting point of this class was to remove all the "less used" functionality that was merged in
on some arbitrary pull requests to the pre-fork repository.  This code is brittle and contains
a lot of "hacks" for a niche set of use cases.  As such, it shouldn't crowd the core functionality
of the ExifTool() class or the stable extended functionality of the ExifToolHelper() class.

The class heirarchy:  ExifTool -> ExifToolHelper -> ExifToolAlpha,
* ExifTool - stable base class with CORE functionality
* ExifToolHelper - user friendly class that extends the base class with general functionality not found in the core
* ExifToolAlpha - alpha-quality code which extends the ExifToolHelper to add functionality that is niche, brittle, or not well tested

Because of this heirarchy, you could always use/extend the ExifToolAlpha() class to have all functionality,
or at your discretion, use one of the more stable classes above.

"""

from .helper import ExifToolHelper


# ======================================================================================================================

#def atexit_handler

# constants related to keywords manipulations
KW_TAGNAME = "IPTC:Keywords"
KW_REPLACE, KW_ADD, KW_REMOVE = range(3)





# ======================================================================================================================



#string helper
def strip_nl(s):
	return ' '.join(s.splitlines())

# ======================================================================================================================

# Error checking function
# very rudimentary checking
# Note: They are quite fragile, because this just parse the output text from exiftool
def check_ok(result):
	"""Evaluates the output from a exiftool write operation (e.g. `set_tags`)

	The argument is the result from the execute method.

	The result is True or False.
	"""
	return not result is None and (not "due to errors" in result)

# ======================================================================================================================

def format_error(result):
	"""Evaluates the output from a exiftool write operation (e.g. `set_tags`)

	The argument is the result from the execute method.

	The result is a human readable one-line string.
	"""
	if check_ok(result):
		return 'exiftool finished probably properly. ("%s")' % strip_nl(result)
	else:
		if result is None:
			return "exiftool operation can't be evaluated: No result given"
		else:
			return 'exiftool finished with error: "%s"' % strip_nl(result)



# ======================================================================================================================

class ExifToolAlpha(ExifToolHelper):
	""" this class extends the ExifToolHelper class with alpha-quality code, which,
	may add functionality, but may introduce bugs or add in unneeded bloat which may
	be specific to niche use cases

	lots of these methods are from the original incarnation of pyexiftool
	with miscellaneous added pull requests.

	There's a lot of extra functionality, but the code quality leaves a lot to be desired

	And in some cases, there are edge cases which return unexpected results... so
	they will be placed into this class until the functionality can be standardized in a "stable" way


	Please issue PR to this class to add functionality, even if not tested well.  This class is for experimental code after all!
	"""

	# ----------------------------------------------------------------------------------------------------------------------
	# i'm not sure if the verification works, but related to pull request (#11)
	def execute_json_wrapper(self, filenames, params=None, retry_on_error=True):
		# make sure the argument is a list and not a single string
		# which would lead to strange errors
		if isinstance(filenames, basestring):
			raise TypeError("The argument 'filenames' must be an iterable of strings")

		execute_params = []

		if params:
			execute_params.extend(params)
		execute_params.extend(filenames)

		result = self.execute_json(execute_params)

		if result:
			try:
				ExifToolAlpha._check_sanity_of_result(filenames, result)
			except (IOError, error):
				# Restart the exiftool child process in these cases since something is going wrong
				self.terminate()
				self.run()

				if retry_on_error:
					result = self.execute_json_filenames(filenames, params, retry_on_error=False)
				else:
					raise error
		else:
			# Reasons for exiftool to provide an empty result, could be e.g. file not found, etc.
			# What should we do in these cases? We don't have any information what went wrong, therefore
			# we just return empty dictionaries.
			result = [{} for _ in filenames]

		return result

	# ----------------------------------------------------------------------------------------------------------------------
	# allows adding additional checks (#11)
	def get_metadata_batch_wrapper(self, filenames, params=None):
		return self.execute_json_wrapper(filenames=filenames, params=params)

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_metadata_wrapper(self, filename, params=None):
		return self.execute_json_wrapper(filenames=[filename], params=params)[0]

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_tags_batch_wrapper(self, tags, filenames, params=None):
		params = (params if params else []) + ["-" + t for t in tags]
		return self.execute_json_wrapper(filenames=filenames, params=params)

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_tags_wrapper(self, tags, filename, params=None):
		return self.get_tags_batch_wrapper(tags, [filename], params=params)[0]

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_tag_batch_wrapper(self, tag, filenames, params=None):
		data = self.get_tags_batch_wrapper([tag], filenames, params=params)
		result = []
		for d in data:
			d.pop("SourceFile")
			result.append(next(iter(d.values()), None))
		return result

	# ----------------------------------------------------------------------------------------------------------------------
	# this was a method with good intentions by the original author, but returns some inconsistent results in some cases
	# for example, if you passed in a single tag, or a group name, it would return the first tag back instead of the whole group
	# try calling get_tag_batch("*.mp4", "QuickTime") or "QuickTime:all" ... the expected results is a dictionary but a single tag is returned
	def get_tag_batch(self, tag, filenames):
		"""Extract a single tag from the given files.

		The first argument is a single tag name, as usual in the
		format <group>:<tag>.

		The second argument is an iterable of file names.

		The return value is a list of tag values or ``None`` for
		non-existent tags, in the same order as ``filenames``.
		"""
		data = self.get_tags(filenames, [tag])
		result = []
		for d in data:
			d.pop("SourceFile")
			result.append(next(iter(d.values()), None))
		return result

	# ----------------------------------------------------------------------------------------------------------------------
	# (#11)
	def get_tag_wrapper(self, tag, filename, params=None):
		return self.get_tag_batch_wrapper(tag, [filename], params=params)[0]

	# ----------------------------------------------------------------------------------------------------------------------
	def get_tag(self, tag, filename):
		"""Extract a single tag from a single file.

		The return value is the value of the specified tag, or
		``None`` if this tag was not found in the file.
		"""
		return self.get_tag_batch(tag, [filename])[0]

	# ----------------------------------------------------------------------------------------------------------------------
	def copy_tags(self, from_filename, to_filename):
		"""Copy all tags from one file to another."""
		params = ["-overwrite_original", "-TagsFromFile", from_filename, to_filename]
		params_utf8 = [x.encode('utf-8') for x in params]
		self.execute(*params_utf8)


	# ----------------------------------------------------------------------------------------------------------------------
	def set_tags_batch(self, tags, filenames):
		"""Writes the values of the specified tags for the given files.

		The first argument is a dictionary of tags and values.  The tag names may
		include group names, as usual in the format <group>:<tag>.

		The second argument is an iterable of file names.

		The format of the return value is the same as for
		:py:meth:`execute()`.

		It can be passed into `check_ok()` and `format_error()`.

		tags items can be lists, in which case, the tag will be passed
		with each item in the list, in the order given
		"""
		# Explicitly ruling out strings here because passing in a
		# string would lead to strange and hard-to-find errors
		if isinstance(tags, basestring):
			raise TypeError("The argument 'tags' must be dictionary "
							"of strings")
		if isinstance(filenames, basestring):
			raise TypeError("The argument 'filenames' must be "
							"an iterable of strings")

		params = []
		params_utf8 = []
		for tag, value in tags.items():
			# contributed by @daviddorme in https://github.com/sylikc/pyexiftool/issues/12#issuecomment-821879234
			# allows setting things like Keywords which require separate directives
			# > exiftool -Keywords=keyword1 -Keywords=keyword2 -Keywords=keyword3 file.jpg
			# which are not supported as duplicate keys in a dictionary
			if isinstance(value, list):
				for item in value:
					params.append(u'-%s=%s' % (tag, item))
			else:
				params.append(u'-%s=%s' % (tag, value))

		params.extend(filenames)
		params_utf8 = [x.encode('utf-8') for x in params]
		return self.execute(*params_utf8)

		#TODO if execute returns data, then error?

	# ----------------------------------------------------------------------------------------------------------------------
	def set_tags(self, tags, filename):
		"""Writes the values of the specified tags for the given file.

		This is a convenience function derived from `set_tags_batch()`.
		Only difference is that it takes as last arugemnt only one file name
		as a string.
		"""
		return self.set_tags_batch(tags, [filename])

	# ----------------------------------------------------------------------------------------------------------------------
	def set_keywords_batch(self, mode, keywords, filenames):
		"""Modifies the keywords tag for the given files.

		The first argument is the operation mode:
		KW_REPLACE: Replace (i.e. set) the full keywords tag with `keywords`.
		KW_ADD:     Add `keywords` to the keywords tag.
					If a keyword is present, just keep it.
		KW_REMOVE:  Remove `keywords` from the keywords tag.
					If a keyword wasn't present, just leave it.

		The second argument is an iterable of key words.

		The third argument is an iterable of file names.

		The format of the return value is the same as for
		:py:meth:`execute()`.

		It can be passed into `check_ok()` and `format_error()`.
		"""
		# Explicitly ruling out strings here because passing in a
		# string would lead to strange and hard-to-find errors
		if isinstance(keywords, basestring):
			raise TypeError("The argument 'keywords' must be "
							"an iterable of strings")
		if isinstance(filenames, basestring):
			raise TypeError("The argument 'filenames' must be "
							"an iterable of strings")

		params = []
		params_utf8 = []

		kw_operation = {KW_REPLACE: "-%s=%s",
						KW_ADD: "-%s+=%s",
						KW_REMOVE: "-%s-=%s"}[mode]

		kw_params = [kw_operation % (KW_TAGNAME, w)  for w in keywords]

		params.extend(kw_params)
		params.extend(filenames)
		logging.debug(params)

		params_utf8 = [x.encode('utf-8') for x in params]
		return self.execute(*params_utf8)

	# ----------------------------------------------------------------------------------------------------------------------
	def set_keywords(self, mode, keywords, filename):
		"""Modifies the keywords tag for the given file.

		This is a convenience function derived from `set_keywords_batch()`.
		Only difference is that it takes as last argument only one file name
		as a string.
		"""
		return self.set_keywords_batch(mode, keywords, [filename])


	# ----------------------------------------------------------------------------------------------------------------------
	@staticmethod
	def _check_sanity_of_result(file_paths, result):
		"""
		Checks if the given file paths matches the 'SourceFile' entries in the result returned by
		exiftool. This is done to find possible mix ups in the streamed responses.
		"""
		# do some sanity checks on the results to make sure nothing was mixed up during reading from stdout
		if len(result) != len(file_paths):
			raise IOError("exiftool did return %d results, but expected was %d" % (len(result), len(file_paths)))
		for i in range(0, len(file_paths)):
			returned_source_file = result[i]['SourceFile']
			requested_file = file_paths[i]
			if returned_source_file != requested_file:
				raise IOError('exiftool returned data for file %s, but expected was %s'
							  % (returned_source_file, requested_file))

	# ----------------------------------------------------------------------------------------------------------------------
