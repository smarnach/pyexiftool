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
import shutil

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


from . import constants

#from pathlib import Path # requires Python 3.4+

import random

# constants to make typos obsolete!
ENCODING_UTF8 = "utf-8"
ENCODING_LATIN1 = "latin-1"

# ======================================================================================================================


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

# ======================================================================================================================

def set_pdeathsig(sig=signal.SIGTERM):
	"""
	Use this method in subprocess.Popen(preexec_fn=set_pdeathsig()) to make sure,
	the exiftool childprocess is stopped if this process dies.
	However, this only works on linux.
	"""
	if constants.PLATFORM_LINUX:
		def callable_method():
			# taken from linux/prctl.h
			pr_set_pdeathsig = 1
			libc = ctypes.CDLL("libc.so.6")
			return libc.prctl(pr_set_pdeathsig, sig)

		return callable_method
	else:
		return None

# ======================================================================================================================



#string helper
def strip_nl (s):
	return ' '.join(s.splitlines())

# ======================================================================================================================

# Error checking function
# very rudimentary checking
# Note: They are quite fragile, because this just parse the output text from exiftool
def check_ok (result):
	"""Evaluates the output from a exiftool write operation (e.g. `set_tags`)

	The argument is the result from the execute method.

	The result is True or False.
	"""
	return not result is None and (not "due to errors" in result)

# ======================================================================================================================

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










# ======================================================================================================================
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

	# ----------------------------------------------------------------------------------------------------------------------
	def __init__(self, executable=None, common_args=None, win_shell=True, return_tuple=False):
		
		random.seed(None) # initialize random number generator
		
		# default settings
		self._executable = None  # executable absolute path
		self._win_shell = win_shell  # do you want to see the shell on Windows?
		self._process = None # this is set to the process to interact with when _running=True
		self._running = False  # is it running?
		
		self._return_tuple = return_tuple # are we returning a tuple in the execute?
		self._last_stdout = None # previous output
		self._last_stderr = None # previous stderr

		# use the passed in parameter, or the default if not set
		# error checking is done in the property.setter
		self.executable = executable if executable is not None else constants.DEFAULT_EXECUTABLE
		
		# set to default block size
		self._block_size = constants.DEFAULT_BLOCK_SIZE
		
		self._common_args = common_args
		# it can't be none, check if it's a list, if not, error

		if common_args is None:
			# default parameters to exiftool
			# -n = disable print conversion (speedup)
			self._common_args = ["-G", "-n"]
		elif type(common_args) is list:
			self._common_args = common_args
		else:
			raise TypeError("common_args not a list of strings")

		self._no_output = '-w' in self._common_args


	# ----------------------------------------------------------------------------------------------------------------------
	def run(self):
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
			warnings.warn("ExifTool already running; doing nothing.", UserWarning)
			return

		# TODO changing common args means it needs a restart, or error, have a restart=True for change common_args or error if running
		proc_args = [self.executable, "-stay_open", "True",  "-@", "-", "-common_args"]
		proc_args.extend(self._common_args) # add the common arguments

		logging.debug(proc_args)
		
		with open(os.devnull, "w") as devnull: # TODO can probably remove or make it a parameter
			try:
				if constants.PLATFORM_WINDOWS:
					startup_info = subprocess.STARTUPINFO()
					if not self._win_shell:
						# Adding enum 11 (SW_FORCEMINIMIZE in win32api speak) will
						# keep it from throwing up a DOS shell when it launches.
						startup_info.dwFlags |= constants.SW_FORCEMINIMIZE

					self._process = subprocess.Popen(
						proc_args,
						stdin=subprocess.PIPE, stdout=subprocess.PIPE,
						stderr=subprocess.PIPE, startupinfo=startup_info) #stderr=devnull
					# TODO check error before saying it's running
				else:
					# assume it's linux
					self._process = subprocess.Popen(
						proc_args,
						stdin=subprocess.PIPE, stdout=subprocess.PIPE,
						stderr=subprocess.PIPE, preexec_fn=set_pdeathsig(signal.SIGTERM)) #stderr=devnull
						# Warning: The preexec_fn parameter is not safe to use in the presence of threads in your application. 
						# https://docs.python.org/3/library/subprocess.html#subprocess.Popen
					# TODO check error before saying it's running
			except FileNotFoundError as fnfe:
				raise fnfe
			except OSError as oe:
				raise oe
			except ValueError as ve:
				raise ve
			except subprocess.CalledProcessError as cpe:
				raise cpe
		
		# check error above before saying it's running
		self._running = True

	# ----------------------------------------------------------------------------------------------------------------------
	def terminate(self, timeout=30, _del=False):
		"""Terminate the ``exiftool`` process of this instance.

		If the subprocess isn't running, this method will do nothing.
		"""
		if not self.running:
			warnings.warn("ExifTool not running; doing nothing.", UserWarning)
			# TODO, maybe add an optional parameter that says ignore_running/check/force or something which will not warn
			return
		
		if _del and constants.PLATFORM_WINDOWS:
			# don't cleanly exit on windows, during __del__ as it'll freeze at communicate()
			self._process.kill()
		else:
			try:
				"""
					On Windows, running this after __del__ freezes at communicate(), regardless of timeout
						this is possibly because the file descriptors are no longer valid or were closed at __del__
						
						test yourself with simple code that calls .run() and then end of script
						
					On Linux, this runs as is, and the process terminates properly
				"""
				self._process.communicate(input=b"-stay_open\nFalse\n", timeout=timeout) # TODO these are constants which should be elsewhere defined
				self._process.kill()
			except subprocess.TimeoutExpired: # this is new in Python 3.3 (for python 2.x, use the PyPI subprocess32 module)
				self._process.kill()
				outs, errs = proc.communicate()
				# err handling code from https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
		
		self._process = None # don't delete, just leave as None
		self._running = False

	# ----------------------------------------------------------------------------------------------------------------------
	def __enter__(self):
		self.run()
		return self

	# ----------------------------------------------------------------------------------------------------------------------
	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.running:
			self.terminate()

	# ----------------------------------------------------------------------------------------------------------------------
	def __del__(self):
		if self.running:
			# indicate that __del__ has been started - allows running alternate code path in terminate()
			self.terminate(_del=True)

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def executable(self):
		return self._executable
	
	@executable.setter
	def executable(self, new_executable):
		"""
		Set the executable.  Does error checking.
		"""
		# cannot set executable when process is running
		if self.running:
			raise RuntimeError( 'Cannot set new executable while Exiftool is running' )
		
		# Python 3.3+ required
		abs_path = shutil.which(new_executable)
		
		if abs_path is None:
			raise FileNotFoundError( '"{}" is not found, on path or as absolute path'.format(new_executable) )
		
		# absolute path is returned
		self._executable = abs_path
	

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def block_size(self):
		return self._block_size
	
	@block_size.setter
	def block_size(self, new_block_size):
		"""
		Set the block_size.  Does error checking.
		"""
		if new_block_size <= 0:
			raise ValueError("Block Size doesn't make sense to be <= 0")
		
		self._block_size = new_block_size

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def running(self):
		# read-only property
		
		if self._running:
			# check if the process is actually alive
			if self._process.poll() is not None:
				# process died
				warnings.warn("ExifTool process was previously running but died")
				self._process = None
				self._running = False
		
		return self._running


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def last_stdout(self):
		"""last output stdout from execute()"""
		return self._last_stdout

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def last_stderr(self):
		"""last output stderr from execute()"""
		return self._last_stderr

	
	# ----------------------------------------------------------------------------------------------------------------------
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
			raise RuntimeError("ExifTool instance not running.")
		
		# constant special sequences when running -stay_open mode
		SEQ_EXECUTE_FMT = "-execute{}\n" # this is the PYFORMAT ... the actual string is b"-execute\n"
		SEQ_READY_FMT = "{{ready{}}}" # this is the PYFORMAT ... the actual string is b"{ready}"
		
		# these are special sequences to help with synchronization.  It will print specific text to STDERR before and after processing
		#SEQ_STDERR_PRE_FMT = "pre{}"
		SEQ_STDERR_POST_FMT = "post{}"
		
		
		# there's a special usage of execute/ready specified in the manual which make almost ensure we are receiving the right signal back
		# from exiftool man pages:  When this number is added, -q no longer suppresses the "{ready}"
		signal_num = random.randint(10000000, 99999999) # arbitrary create a 8 digit number
		seq_execute = SEQ_EXECUTE_FMT.format(signal_num).encode(ENCODING_UTF8)
		seq_ready = SEQ_READY_FMT.format(signal_num).encode(ENCODING_UTF8)
		
		#seq_err_pre = SEQ_STDERR_PRE_FMT.format(signal_num).encode(ENCODING_UTF8)
		seq_err_post = SEQ_STDERR_POST_FMT.format(signal_num).encode(ENCODING_UTF8)
		
		cmd_text = b"\n".join(params + (b"-echo4",seq_err_post, seq_execute,))
		# cmd_text.encode("utf-8") # a commit put this in the next line, but i can't get it to work TODO
		# might look at something like this https://stackoverflow.com/questions/7585435/best-way-to-convert-string-to-bytes-in-python-3
		self._process.stdin.write(cmd_text)
		self._process.stdin.flush()
		
		fdout = self._process.stdout.fileno()
		output = ExifTool._read_fd_endswith(fdout, seq_ready, self._block_size)
		
		# when it's ready, we can safely read all of stderr out, as the command is already done
		fderr = self._process.stderr.fileno()
		outerr = ExifTool._read_fd_endswith(fderr, seq_err_post, self._block_size)
		
		# save the output to class vars for retrieval
		self._last_stdout = output.strip()[:-len(seq_ready)]
		self._last_stderr = outerr.strip()[:-len(seq_err_post)]
		
		if self._return_tuple:
			return (self._last_stdout, self._last_stderr,)
		else:
			# this was the standard return before, just stdout
			return self._last_stdout


	# ----------------------------------------------------------------------------------------------------------------------
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
		std = self.execute(b"-j", *params)
		
		if self._return_tuple:
			res = std[0]
		else:
			res = std
		
		if len(res) == 0:
			# if the command has no files it's worked on, or some other type of error
			# we can either return None, or [], or FileNotFoundError ..
			
			# but, since it's technically not an error to have no files, 
			# returning None is the best.  
			# Even [] could be ambugious if Exiftool changes the returned JSON structure in the future
			# TODO haven't decided on [] or None yet
			return None
		
		
		try:
			res_decoded = res.decode(ENCODING_UTF8)
		except UnicodeDecodeError:
			res_decoded = res.decode(ENCODING_LATIN1)
		# TODO res_decoded can be invalid json if `-w` flag is specified in common_args
		# which will return something like
		# image files read
		# output files created
		if self._no_output:
			print(res_decoded)
		else:
			# TODO: if len(res_decoded) == 0, then there's obviously an error here
			return json.loads(res_decoded)


	# ----------------------------------------------------------------------------------------------------------------------
	@staticmethod
	def _read_fd_endswith(fd, b_endswith, block_size):
		""" read an fd and keep reading until it endswith the seq_ends 
			
			this allows a consolidated read function that is platform indepdent
			
			if you're not careful, on windows, this will block
		"""
		output = b""
		endswith_count = len(b_endswith) + 4 # if we're only looking at the last few bytes, make it meaningful.  4 is max size of \r\n? (or 2)
		
		# I believe doing a splice, then a strip is more efficient in memory hence the original code did it this way.
		# need to benchmark to see if in large strings, strip()[-endswithcount:] is more expensive
		while not output[-endswith_count:].strip().endswith(b_endswith):
			if constants.PLATFORM_WINDOWS:
				# windows does not support select() for anything except sockets
				# https://docs.python.org/3.7/library/select.html
				output += os.read(fd, block_size)
			else:
				# this does NOT work on windows... and it may not work on other systems... in that case, put more things to use the original code above
				inputready,outputready,exceptready = select.select([fd], [], [])
				for i in inputready:
					if i == fd:
						output += os.read(fd, block_size)
		
		return output
