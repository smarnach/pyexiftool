# -*- coding: utf-8 -*-
# PyExifTool <http://github.com/smarnach/pyexiftool>
# Copyright 2012 Sven Marnach.
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
PyExifTool is a Python library to communicate with an instance of Phil
Harvey's excellent ExifTool_ command-line application.  The library
provides the class :py:class:`ExifTool` that runs the command-line
tool in batch mode and features methods to send commands to that
program, including methods to extract meta-information from one or
more image files.  Since ``exiftool`` is run in batch mode, only a
single instance needs to be launched and can be reused for many
queries.  This is much more efficient than launching a separate
process for every single query.

.. _ExifTool: http://www.sno.phy.queensu.ca/~phil/exiftool/

The source code can be checked out from the github repository with

::

	git clone git://github.com/smarnach/pyexiftool.git

Alternatively, you can download a tarball_.  There haven't been any
releases yet.

.. _tarball: https://github.com/smarnach/pyexiftool/tarball/master

PyExifTool is licenced under GNU GPL version 3 or later.

Example usage::

	import exiftool

	files = ["a.jpg", "b.png", "c.tif"]
	with exiftool.ExifTool() as et:
		metadata = et.get_metadata_batch(files)
	for d in metadata:
		print("{:20.20} {:20.20}".format(d["SourceFile"],
										 d["EXIF:DateTimeOriginal"]))
"""

from __future__ import unicode_literals

import select
import sys
import subprocess
import os
try:
	import ujson as json
except ImportError:
	import json
import warnings
import logging
import codecs

# for the pdeathsig
import signal
import ctypes

try:        # Py3k compatibility
	basestring
except NameError:
	basestring = (bytes, str)






# specify the extension so exiftool doesn't default to running "exiftool.py" on windows (which could happen)
if sys.platform == 'win32':
	DEFAULT_EXECUTABLE = "exiftool.exe"
else:
	DEFAULT_EXECUTABLE = "exiftool"
"""The name of the executable to run.

If the executable is not located in one of the paths listed in the
``PATH`` environment variable, the full path should be given here.
"""

# Sentinel indicating the end of the output of a sequence of commands.
# The standard value should be fine.
sentinel = b"{ready}"

# The block size when reading from exiftool.  The standard value
# should be fine, though other values might give better performance in
# some cases.
block_size = 4096

# constants related to keywords manipulations
KW_TAGNAME = "IPTC:Keywords"
KW_REPLACE, KW_ADD, KW_REMOVE = range(3)

#------------------------------------------------------------------------------------------------


# This code has been adapted from Lib/os.py in the Python source tree
# (sha1 265e36e277f3)
def _fscodec():
	encoding = sys.getfilesystemencoding()
	errors = "strict"
	if encoding != "mbcs":
		try:
			codecs.lookup_error("surrogateescape")
		except LookupError:
			pass
		else:
			errors = "surrogateescape"

	def fsencode(filename):
		"""
		Encode filename to the filesystem encoding with 'surrogateescape' error
		handler, return bytes unchanged. On Windows, use 'strict' error handler if
		the file system encoding is 'mbcs' (which is the default encoding).
		"""
		if isinstance(filename, bytes):
			return filename
		else:
			return filename.encode(encoding, errors)

	return fsencode

fsencode = _fscodec()
del _fscodec

#------------------------------------------------------------------------------------------------

def set_pdeathsig(sig=signal.SIGTERM):
	"""
	Use this method in subprocess.Popen(preexec_fn=set_pdeathsig()) to make sure,
	the exiftool childprocess is stopped if this process dies.
	However, this only works on linux.
	"""
	if sys.platform == "linux" or sys.platform == "linux2":
		def callable_method():
			# taken from linux/prctl.h
			pr_set_pdeathsig = 1
			libc = ctypes.CDLL("libc.so.6")
			return libc.prctl(pr_set_pdeathsig, sig)

		return callable_method
	else:
		return None




#string helper
def strip_nl (s):
	return ' '.join(s.splitlines())


# Error checking function
# very rudimentary checking
# Note: They are quite fragile, because this just parse the output text from exiftool
def check_ok (result):
	"""Evaluates the output from a exiftool write operation (e.g. `set_tags`)

	The argument is the result from the execute method.

	The result is True or False.
	"""
	return not result is None and (not "due to errors" in result)

def format_error (result):
	"""Evaluates the output from a exiftool write operation (e.g. `set_tags`)

	The argument is the result from the execute method.

	The result is a human readable one-line string.
	"""
	if check_ok (result):
		return 'exiftool finished probably properly. ("%s")' % strip_nl(result)
	else:
		if result is None:
			return "exiftool operation can't be evaluated: No result given"
		else:
			return 'exiftool finished with error: "%s"' % strip_nl(result)




#------------------------------------------------------------------------------------------------


# https://gist.github.com/techtonik/4368898
# Public domain code by anatoly techtonik <techtonik@gmail.com>
# AKA Linux `which` and Windows `where`

def find_executable(executable, path=None):
	"""Find if 'executable' can be run. Looks for it in 'path'
	(string that lists directories separated by 'os.pathsep';
	defaults to os.environ['PATH']). Checks for all executable
	extensions. Returns full path or None if no command is found.
	"""
	if path is None:
		path = os.environ['PATH']
	paths = path.split(os.pathsep)
	extlist = ['']
	
	if os.name == 'os2':
		(base, ext) = os.path.splitext(executable)
		# executable files on OS/2 can have an arbitrary extension, but
		# .exe is automatically appended if no dot is present in the name
		if not ext:
			executable = executable + ".exe"
	elif sys.platform == 'win32':
		pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
		(base, ext) = os.path.splitext(executable)
		if ext.lower() not in pathext:
			extlist = pathext
	
	for ext in extlist:
		execname = executable + ext
		#print(execname)
		if os.path.isfile(execname):
			return execname
		else:
			for p in paths:
				f = os.path.join(p, execname)
				if os.path.isfile(f):
					return f
	else:
		return None



#------------------------------------------------------------------------------------------------
class ExifTool(object):
	"""Run the `exiftool` command-line tool and communicate to it.

	The argument ``print_conversion`` determines whether exiftool should
	perform print conversion, which prints values in a human-readable way but
	may be slower. If print conversion is enabled, appending ``#`` to a tag
	name disables the print conversion for this particular tag.

	You can pass two arguments to the constructor:
	- ``common_args`` (list of strings): contains additional paramaters for
	  the stay-open instance of exiftool
	- ``executable`` (string): file name of the ``exiftool`` executable.
	  The default value ``exiftool`` will only work if the executable
	  is in your ``PATH``

	Most methods of this class are only available after calling
	:py:meth:`start()`, which will actually launch the subprocess.  To
	avoid leaving the subprocess running, make sure to call
	:py:meth:`terminate()` method when finished using the instance.
	This method will also be implicitly called when the instance is
	garbage collected, but there are circumstance when this won't ever
	happen, so you should not rely on the implicit process
	termination.  Subprocesses won't be automatically terminated if
	the parent process exits, so a leaked subprocess will stay around
	until manually killed.

	A convenient way to make sure that the subprocess is terminated is
	to use the :py:class:`ExifTool` instance as a context manager::

		with ExifTool() as et:
			...

	.. warning:: Note that there is no error handling.  Nonsensical
	   options will be silently ignored by exiftool, so there's not
	   much that can be done in that regard.  You should avoid passing
	   non-existent files to any of the methods, since this will lead
	   to undefied behaviour.

	.. py:attribute:: running

	   A Boolean value indicating whether this instance is currently
	   associated with a running subprocess.
	"""

	def __init__(self, executable_=None, common_args=None, win_shell=True, config_file=None):

		self.win_shell = win_shell

		if executable_ is None:
			self.executable = DEFAULT_EXECUTABLE
		else:
			self.executable = executable_
		
		# error checking
		if find_executable(self.executable) is None:
			raise FileNotFoundError( '"{}" is not found, on path or as absolute path'.format(self.executable) )
		
		self.running = False

		self._common_args = common_args
		# it can't be none, check if it's a list, if not, error

		if config_file and not os.path.exists(config_file):
			raise FileNotFoundError("The config file could not be found")

		self._config_file = config_file

		self._process = None

		if common_args is None:
			# default parameters to exiftool
			# -n = disable print conversion (speedup)
			self.common_args = ["-G", "-n"]
		elif type(common_args) is list:
			self.common_args = common_args
		else:
			raise TypeError("common_args not a list of strings")

		self.no_output = '-w' in self.common_args

		# sets logger with name rather than using the root logger
		self.logger = logging.getLogger(__name__)


	def start(self):
		"""Start an ``exiftool`` process in batch mode for this instance.

		This method will issue a ``UserWarning`` if the subprocess is
		already running.  The process is by default started with the ``-G`` 
		and ``-n`` (print conversion disabled) as common arguments,
		which are automatically included in every command you run with
		:py:meth:`execute()`.

		However, you can override these default arguments with the 
		``common_args`` parameter in the constructor.
		"""
		if self.running:
			warnings.warn("ExifTool already running; doing nothing.")
			return

		proc_args = [self.executable, ]
		# If working with a config file, it must be the first argument after the executable per: https://exiftool.org/config.html
		if self._config_file:
			proc_args.extend(["-config", self._config_file])
		proc_args.extend(["-stay_open", "True", "-@", "-", "-common_args"])
		proc_args.extend(self.common_args)  # add the common arguments

		self.logger.debug(proc_args)
		
		with open(os.devnull, "w") as devnull:
			try:
				if sys.platform == 'win32':
					startup_info = subprocess.STARTUPINFO()
					if not self.win_shell:
						SW_FORCEMINIMIZE = 11 # from win32con
						# Adding enum 11 (SW_FORCEMINIMIZE in win32api speak) will
						# keep it from throwing up a DOS shell when it launches.
						startup_info.dwFlags |= 11

					self._process = subprocess.Popen(
						proc_args,
						stdin=subprocess.PIPE, stdout=subprocess.PIPE,
						stderr=devnull, startupinfo=startup_info)
					# TODO check error before saying it's running
				else:
					# assume it's linux
					self._process = subprocess.Popen(
						proc_args,
						stdin=subprocess.PIPE, stdout=subprocess.PIPE,
						stderr=devnull, preexec_fn=set_pdeathsig(signal.SIGTERM))
						# Warning: The preexec_fn parameter is not safe to use in the presence of threads in your application. 
						# https://docs.python.org/3/library/subprocess.html#subprocess.Popen
			except FileNotFoundError as fnfe:
				raise fnfe
			except OSError as oe:
				raise oe
			except ValueError as ve:
				raise ve
			except subprocess.CalledProcessError as cpe:
				raise cpe
		
		# check error above before saying it's running
		self.running = True

	def terminate(self, wait_timeout=30):
		"""Terminate the ``exiftool`` process of this instance.

		If the subprocess isn't running, this method will do nothing.
		"""
		if not self.running:
			return
		self._process.stdin.write(b"-stay_open\nFalse\n")
		self._process.stdin.flush()
		try:
			self._process.communicate(timeout=wait_timeout)
		except subprocess.TimeoutExpired: # this is new in Python 3.3 (for python 2.x, use the PyPI subprocess32 module)
			self._process.kill()
			outs, errs = self._process.communicate()
			# err handling code from https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
			
		del self._process
		self.running = False

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.terminate()

	def __del__(self):
		self.terminate()

	def execute(self, *params):
		"""Execute the given batch of parameters with ``exiftool``.

		This method accepts any number of parameters and sends them to
		the attached ``exiftool`` process.  The process must be
		running, otherwise ``ValueError`` is raised.  The final
		``-execute`` necessary to actually run the batch is appended
		automatically; see the documentation of :py:meth:`start()` for
		the common options.  The ``exiftool`` output is read up to the
		end-of-output sentinel and returned as a raw ``bytes`` object,
		excluding the sentinel.

		The parameters must also be raw ``bytes``, in whatever
		encoding exiftool accepts.  For filenames, this should be the
		system's filesystem encoding.

		.. note:: This is considered a low-level method, and should
		   rarely be needed by application developers.
		"""
		if not self.running:
			raise ValueError("ExifTool instance not running.")
		
		cmd_text = b"\n".join(params + (b"-execute\n",))
		# cmd_text.encode("utf-8") # a commit put this in the next line, but i can't get it to work TODO
		# might look at something like this https://stackoverflow.com/questions/7585435/best-way-to-convert-string-to-bytes-in-python-3
		self._process.stdin.write(cmd_text)
		self._process.stdin.flush()
		output = b""
		fd = self._process.stdout.fileno()
		while not output[-32:].strip().endswith(sentinel):
			if sys.platform == 'win32':
				# windows does not support select() for anything except sockets
				# https://docs.python.org/3.7/library/select.html
				output += os.read(fd, block_size)
			else:
				# this does NOT work on windows... and it may not work on other systems... in that case, put more things to use the original code above
				inputready,outputready,exceptready = select.select([fd],[],[])
				for i in inputready:
					if i == fd:
						output += os.read(fd, block_size)
		return output.strip()[:-len(sentinel)]


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
				ExifTool._check_sanity_of_result(filenames, result)
			except IOError as error:
				# Restart the exiftool child process in these cases since something is going wrong
				self.terminate()
				self.start()

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



	def execute_json(self, *params):
		"""Execute the given batch of parameters and parse the JSON output.

		This method is similar to :py:meth:`execute()`.  It
		automatically adds the parameter ``-j`` to request JSON output
		from ``exiftool`` and parses the output.  The return value is
		a list of dictionaries, mapping tag names to the corresponding
		values.  All keys are Unicode strings with the tag names
		including the ExifTool group name in the format <group>:<tag>.
		The values can have multiple types.  All strings occurring as
		values will be Unicode strings.  Each dictionary contains the
		name of the file it corresponds to in the key ``"SourceFile"``.

		The parameters to this function must be either raw strings
		(type ``str`` in Python 2.x, type ``bytes`` in Python 3.x) or
		Unicode strings (type ``unicode`` in Python 2.x, type ``str``
		in Python 3.x).  Unicode strings will be encoded using
		system's filesystem encoding.  This behaviour means you can
		pass in filenames according to the convention of the
		respective Python version – as raw strings in Python 2.x and
		as Unicode strings in Python 3.x.
		"""
		params = map(fsencode, params)
		# Some latin bytes won't decode to utf-8.
		# Try utf-8 and fallback to latin.
		# http://stackoverflow.com/a/5552623/1318758
		# https://github.com/jmathai/elodie/issues/127
		res = self.execute(b"-j", *params)
		try:
			res_decoded = res.decode("utf-8")
		except UnicodeDecodeError:
			res_decoded = res.decode("latin-1")
		# res_decoded can be invalid json if `-w` flag is specified in common_args
		# which will return something like
		# image files read
		# output files created
		if self.no_output:
			print(res_decoded)
		else:
			# TODO: if len(res_decoded) == 0, then there's obviously an error here
			return json.loads(res_decoded)

	# allows adding additional checks (#11)
	def get_metadata_batch_wrapper(self, filenames, params=None):
		return self.execute_json_wrapper(filenames=filenames, params=params)

	def get_metadata_batch(self, filenames, params=None):
		"""Return all meta-data for the given files.

		The return value will have the format described in the
		documentation of :py:meth:`execute_json()`.
		"""
		if not params:
			params = []
		return self.execute_json(*filenames, *params)

	# (#11)
	def get_metadata_wrapper(self, filename, params=None):
		return self.execute_json_wrapper(filenames=[filename], params=params)[0]

	def get_metadata(self, filename, params=None):
		"""Return meta-data for a single file.

		The returned dictionary has the format described in the
		documentation of :py:meth:`execute_json()`.
		"""
		if not params:
			params = []
		return self.execute_json(filename, *params)[0]

	# (#11)
	def get_tags_batch_wrapper(self, tags, filenames, params=None):
		params = (params if params else []) + ["-" + t for t in tags]
		return self.execute_json_wrapper(filenames=filenames, params=params)

	def get_tags_batch(self, tags, filenames):
		"""Return only specified tags for the given files.

		The first argument is an iterable of tags.  The tag names may
		include group names, as usual in the format <group>:<tag>.

		The second argument is an iterable of file names.

		The format of the return value is the same as for
		:py:meth:`execute_json()`.
		"""
		# Explicitly ruling out strings here because passing in a
		# string would lead to strange and hard-to-find errors
		if isinstance(tags, basestring):
			raise TypeError("The argument 'tags' must be "
							"an iterable of strings")
		if isinstance(filenames, basestring):
			raise TypeError("The argument 'filenames' must be "
							"an iterable of strings")
		params = ["-" + t for t in tags]
		params.extend(filenames)
		return self.execute_json(*params)

	# (#11)
	def get_tags_wrapper(self, tags, filename, params=None):
		return self.get_tags_batch_wrapper(tags, [filename], params=params)[0]

	def get_tags(self, tags, filename):
		"""Return only specified tags for a single file.

		The returned dictionary has the format described in the
		documentation of :py:meth:`execute_json()`.
		"""
		return self.get_tags_batch(tags, [filename])[0]

	# (#11)
	def get_tag_batch_wrapper(self, tag, filenames, params=None):
		data = self.get_tags_batch_wrapper([tag], filenames, params=params)
		result = []
		for d in data:
			d.pop("SourceFile")
			result.append(next(iter(d.values()), None))
		return result


	def get_tag_batch(self, tag, filenames):
		"""Extract a single tag from the given files.

		The first argument is a single tag name, as usual in the
		format <group>:<tag>.

		The second argument is an iterable of file names.

		The return value is a list of tag values or ``None`` for
		non-existent tags, in the same order as ``filenames``.
		"""
		data = self.get_tags_batch([tag], filenames)
		result = []
		for d in data:
			d.pop("SourceFile")
			result.append(next(iter(d.values()), None))
		return result

	# (#11)
	def get_tag_wrapper(self, tag, filename, params=None):
		return self.get_tag_batch_wrapper(tag, [filename], params=params)[0]

	def get_tag(self, tag, filename):
		"""Extract a single tag from a single file.

		The return value is the value of the specified tag, or
		``None`` if this tag was not found in the file.
		"""
		return self.get_tag_batch(tag, [filename])[0]

	def copy_tags(self, fromFilename, toFilename):
		"""Copy all tags from one file to another."""
		params = ["-overwrite_original", "-TagsFromFile", fromFilename, toFilename]
		params_utf8 = [x.encode('utf-8') for x in params]
		self.execute(*params_utf8)


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

	def set_tags(self, tags, filename):
		"""Writes the values of the specified tags for the given file.

		This is a convenience function derived from `set_tags_batch()`.
		Only difference is that it takes as last arugemnt only one file name
		as a string.
		"""
		return self.set_tags_batch(tags, [filename])

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

		kw_operation = {KW_REPLACE:"-%s=%s",
						KW_ADD:"-%s+=%s",
						KW_REMOVE:"-%s-=%s"}[mode]

		kw_params = [ kw_operation % (KW_TAGNAME, w)  for w in keywords ]

		params.extend(kw_params)
		params.extend(filenames)
		self.logger.debug(params)

		params_utf8 = [x.encode('utf-8') for x in params]
		return self.execute(*params_utf8)

	def set_keywords(self, mode, keywords, filename):
		"""Modifies the keywords tag for the given file.

		This is a convenience function derived from `set_keywords_batch()`.
		Only difference is that it takes as last argument only one file name
		as a string.
		"""
		return self.set_keywords_batch(mode, keywords, [filename])



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
