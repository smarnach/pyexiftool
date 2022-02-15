# -*- coding: utf-8 -*-
# PyExifTool <http://github.com/sylikc/pyexiftool>
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

.. _ExifTool: https://exiftool.org

The source code can be checked out from the github repository with

::

	git clone git://github.com/sylikc/pyexiftool.git

Alternatively, you can download a tarball_.  There haven't been any
releases yet.

.. _tarball: https://github.com/sylikc/pyexiftool/tarball/master

PyExifTool is licenced under GNU GPL version 3 or later, or BSD license.

Example usage::

	import exiftool

	files = ["a.jpg", "b.png", "c.tif"]
	with exiftool.ExifToolHelper() as et:
		metadata = et.get_metadata(files)
	for d in metadata:
		print("{:20.20} {:20.20}".format(d["SourceFile"],
										 d["EXIF:DateTimeOriginal"]))
"""

# ---------- standard Python imports ----------
import select
import subprocess
import os
import shutil
from pathlib import Path  # requires Python 3.4+
import random
import locale

# for the pdeathsig
import signal
import ctypes


# ---------- UltraJSON overloaded import ----------

try:
	# Optional UltraJSON library - ultra-fast JSON encoder/decoder, drop-in replacement
	import ujson as json
except ImportError:
	import json  # type: ignore   # comment related to https://github.com/python/mypy/issues/1153
import warnings



# ---------- Linting Imports ----------
# for static analysis / type checking - Python 3.5+
from collections.abc import Callable
from typing import Optional, List



# ---------- Library Package Imports ----------

from . import constants


# ======================================================================================================================


# constants to make typos obsolete!
ENCODING_UTF8: str = "utf-8"
#ENCODING_LATIN1: str = "latin-1"


# ======================================================================================================================

def _set_pdeathsig(sig) -> Optional[Callable]:
	"""
	Use this method in subprocess.Popen(preexec_fn=set_pdeathsig()) to make sure,
	the exiftool childprocess is stopped if this process dies.
	However, this only works on linux.
	"""
	if constants.PLATFORM_LINUX:
		def callable_method():
			libc = ctypes.CDLL("libc.so.6")
			return libc.prctl(constants.PR_SET_PDEATHSIG, sig)

		return callable_method
	else:
		return None


# ======================================================================================================================

def _read_fd_endswith(fd, b_endswith, block_size: int):
	""" read an fd and keep reading until it endswith the seq_ends

		this allows a consolidated read function that is platform indepdent

		if you're not careful, on windows, this will block
	"""
	output = b""

	# if we're only looking at the last few bytes, make it meaningful.  4 is max size of \r\n? (or 2)
	# this value can be bigger to capture more bytes at the "tail" of the read, but if it's too small, the whitespace might miss the detection
	endswith_count = len(b_endswith) + 4

	# I believe doing a splice, then a strip is more efficient in memory hence the original code did it this way.
	# need to benchmark to see if in large strings, strip()[-endswithcount:] is more expensive or not
	while not output[-endswith_count:].strip().endswith(b_endswith):
		if constants.PLATFORM_WINDOWS:
			# windows does not support select() for anything except sockets
			# https://docs.python.org/3.7/library/select.html
			output += os.read(fd, block_size)
		else:  # pytest-cov:windows: no cover
			# this does NOT work on windows... and it may not work on other systems... in that case, put more things to use the original code above
			inputready, outputready, exceptready = select.select([fd], [], [])
			for i in inputready:
				if i == fd:
					output += os.read(fd, block_size)

	return output






# ======================================================================================================================

class ExifTool(object):
	"""Run the `exiftool` command-line tool and communicate with it.

	There argument ``print_conversion`` no longer exists.  Use ``common_args``
	to enable/disable print conversion by specifying or not ``-n``.
	This determines whether exiftool should perform print conversion,
	which prints values in a human-readable way but
	may be slower. If print conversion is enabled, appending ``#`` to a tag
	name disables the print conversion for this particular tag.
	See Exiftool documentation for more details:  https://exiftool.org/faq.html#Q6

	You can pass optional arguments to the constructor:
	- ``executable`` (string): file name of the ``exiftool`` executable.
	  The default value ``exiftool`` will only work if the executable
	  is in your ``PATH``
	  You can also specify the full path to the ``exiftool`` executable.
	  See :py:attr:`executable` property for more details.
	- ``common_args`` (list of strings): contains additional paramaters for
	  the stay-open instance of exiftool.  The default is ``-G`` and ``-n``.
	  Read the exiftool documenation to get further information on what the
	  args do:  https://exiftool.org/exiftool_pod.html
	- ``win_shell``
	- ``config_file`` (string): file path to ``-config`` parameter when
	  starting process.
	  See :py:attr:`config_file` property for more details.
	- ``encoding`` (string): encoding to be used when communicating with
	  exiftool process.  By default, will use ``locale.getpreferredencoding()``
	  See :py:attr:`encoding` property for more details
	- ``logger`` (object):  Set a custom logger to log status and debug messages to.
	  See :py:meth:``_set_logger()` for more details.

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
	   to undefined behaviour.

	.. py:attribute:: _running

	   A Boolean value indicating whether this instance is currently
	   associated with a running subprocess.
	"""

	##############################################################################
	#################################### INIT ####################################
	##############################################################################

	# ----------------------------------------------------------------------------------------------------------------------

	def __init__(self,
	  executable: Optional[str] = None,
	  common_args: Optional[List[str]] = ["-G", "-n"],
	  win_shell: bool = False,
	  config_file: Optional[str] = None,
	  encoding = None,
	  logger = None) -> None:
		""" common_args defaults to -G -n as this is the most common use case.
		-n improves the speed, and consistency of output is more machine-parsable
		-G separates the grouping
		"""

		# --- default settings / declare member variables ---
		self._running: bool = False  # is it running?
		self._win_shell: bool = win_shell  # do you want to see the shell on Windows?

		self._process = None  # this is set to the process to interact with when _running=True
		self._ver = None  # this is set to be the exiftool -v -ver when running

		self._last_stdout: Optional[str] = None  # previous output
		self._last_stderr: Optional[str] = None  # previous stderr
		self._last_status: Optional[int] = None  # previous exit status from exiftool (look up EXIT STATUS in exiftool documentation for more information)

		self._block_size: int = constants.DEFAULT_BLOCK_SIZE  # set to default block size


		# these are set via properties
		self._executable: Optional[str] = None  # executable absolute path
		self._config_file: Optional[str] = None  # config file that can only be set when exiftool is not running
		self._common_args: Optional[List[str]] = None
		self._no_output = None  # TODO examine whether this is needed
		self._logger = None
		self._encoding = None



		# --- run external library initialization code ---
		random.seed(None)  # initialize random number generator




		# --- set variables via properties (which do the error checking) --

		# set first, so that debug and info messages get logged
		self.logger = logger

		# use the passed in parameter, or the default if not set
		# error checking is done in the property.setter
		self.executable = executable or constants.DEFAULT_EXECUTABLE
		self.encoding = encoding
		self.common_args = common_args

		# set the property, error checking happens in the property.setter
		self.config_file = config_file




	#######################################################################################
	#################################### MAGIC METHODS ####################################
	#######################################################################################

	# ----------------------------------------------------------------------------------------------------------------------

	def __enter__(self):
		self.run()
		return self

	# ----------------------------------------------------------------------------------------------------------------------
	def __exit__(self, exc_type, exc_val, exc_tb) -> None:
		if self.running:
			self.terminate()

	# ----------------------------------------------------------------------------------------------------------------------
	def __del__(self) -> None:
		if self.running:
			# indicate that __del__ has been started - allows running alternate code path in terminate()
			self.terminate(_del=True)




	########################################################################################
	#################################### PROPERTIES R/w ####################################
	########################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def executable(self):
		return self._executable

	@executable.setter
	def executable(self, new_executable) -> None:
		"""
		Set the executable.  Does error checking.
		You can specify just the executable name, or a full path
		"""
		# cannot set executable when process is running
		if self.running:
			raise RuntimeError("Cannot set new executable while Exiftool is running")

		abs_path: Optional[str] = None

		# in testing, shutil.which() will work if a complete path is given,
		# but this isn't clear from documentation, so we explicitly check and
		# don't search if path exists
		if Path(new_executable).exists():
			abs_path = new_executable
		else:
			# Python 3.3+ required
			abs_path = shutil.which(new_executable)

			if abs_path is None:
				raise FileNotFoundError(f'"{new_executable}" is not found, on path or as absolute path')

		# absolute path is returned
		self._executable = abs_path

		if self._logger: self._logger.info(f"Property 'executable': set to \"{abs_path}\"")


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def encoding(self):
		return self._encoding

	@encoding.setter
	def encoding(self, new_encoding) -> None:
		"""
		Set the encoding of Popen() communication with exiftool process.  Does error checking.

		if new_encoding is None, will detect it from locale.getpreferredencoding(do_setlocale=False)
		do_setlocale is set to False as not to affect a caller.  will default to UTF-8 if nothing comes back

		this does NOT validate the encoding for validity.  It is passed verbatim into subprocess.Popen()
		"""

		# cannot set executable when process is running
		if self.running:
			raise RuntimeError("Cannot set new executable while Exiftool is running")

		# auto-detect system specific
		self._encoding = new_encoding or (locale.getpreferredencoding(do_setlocale=False) or ENCODING_UTF8)


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def block_size(self) -> int:
		return self._block_size

	@block_size.setter
	def block_size(self, new_block_size: int) -> None:
		"""
		Set the block_size.  Does error checking.
		"""
		if new_block_size <= 0:
			raise ValueError("Block Size doesn't make sense to be <= 0")

		self._block_size = new_block_size

		if self._logger: self._logger.info(f"Property 'block_size': set to \"{new_block_size}\"")


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def common_args(self) -> Optional[List[str]]:
		return self._common_args

	@common_args.setter
	def common_args(self, new_args: Optional[List[str]]) -> None:
		""" set the common_args parameter

			this is the common_args that is passed when the Exiftool process is STARTED
			see "-common_args" parameter in Exiftool documentation https://exiftool.org/exiftool_pod.html

			so, if running==True, it will throw an error.  Can only set common_args when exiftool is not running

			If new_args is None, will set to []
		"""

		if self.running:
			raise RuntimeError("Cannot set new common_args while exiftool is running!")

		if new_args is None:
			self._common_args = []
		elif isinstance(new_args, list):
			# default parameters to exiftool
			# -n = disable print conversion (speedup)
			self._common_args = new_args
		else:
			raise TypeError("common_args not a list of strings")

		# TODO examine if this is still a needed thing
		self._no_output = '-w' in self._common_args

		if self._logger: self._logger.info(f"Property 'common_args': set to \"{self._common_args}\"")


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def config_file(self) -> Optional[str]:
		return self._config_file

	@config_file.setter
	def config_file(self, new_config_file: Optional[str]) -> None:
		""" set the config_file parameter

		if running==True, it will throw an error.  Can only set config_file when exiftool is not running
		"""
		if self.running:
			raise RuntimeError("Cannot set a new config_file while exiftool is running!")

		if new_config_file is None:
			self._config_file = None
		elif not Path(new_config_file).exists():
			raise FileNotFoundError("The config file could not be found")
		else:
			self._config_file = new_config_file

		if self._logger: self._logger.info(f"Property 'config_file': set to \"{self._config_file}\"")



	##############################################################################################
	#################################### PROPERTIES Read only ####################################
	##############################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def running(self) -> bool:
		# read-only property

		if self._running:
			# check if the process is actually alive
			if self._process.poll() is not None:
				# process died
				warnings.warn("ExifTool process was previously running but died")
				self._flag_running_false()

				if self._logger: self._logger.warning(f"Property 'running': ExifTool process was previously running but died")

		return self._running


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def version(self) -> str:
		""" returns a string from -ver """

		if not self.running:
			raise RuntimeError("Can't get ExifTool version when it's not running!")

		return self._ver

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def last_stdout(self) -> Optional[str]:
		"""last output stdout from execute()
		currently it is INTENTIONALLY _NOT_ CLEARED on exiftool termination and not dependent on running state
		This allows for executing a command and terminating, but still haven't last* around."""
		return self._last_stdout

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def last_stderr(self) -> Optional[str]:
		"""last output stderr from execute()
		currently it is INTENTIONALLY _NOT_ CLEARED on exiftool termination and not dependent on running state
		This allows for executing a command and terminating, but still haven't last* around."""
		return self._last_stderr

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def last_status(self) -> Optional[int]:
		"""last exit status from execute()
		currently it is INTENTIONALLY _NOT_ CLEARED on exiftool termination and not dependent on running state
		This allows for executing a command and terminating, but still haven't last* around."""
		return self._last_status




	###############################################################################################
	#################################### PROPERTIES Write only ####################################
	###############################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	def _set_logger(self, new_logger) -> None:
		""" set a new user-created logging.Logger object
			can be set at any time to start logging.

			Set to None at any time to stop logging
		"""
		if new_logger is None:
			self._logger = None
			return

		# can't check this in case someone passes a drop-in replacement, like loguru, which isn't type logging.Logger
		#elif not isinstance(new_logger, logging.Logger):
		#	raise TypeError("logger needs to be of type logging.Logger")


		# do some basic checks on methods available in the "logger" provided
		check = True
		try:
			# ExifTool will probably use all of these logging method calls at some point
			# check all these are callable methods
			check = callable(new_logger.info) and \
				callable(new_logger.warning) and \
				callable(new_logger.error) and \
				callable(new_logger.critical) and \
				callable(new_logger.exception)
		except AttributeError as e:
			check = False

		if not check:
			raise TypeError("logger needs to implement methods (info,warning,error,critical,exception)")

		self._logger = new_logger

	# have to run this at the class level to create a special write-only property
	# https://stackoverflow.com/questions/17576009/python-class-property-use-setter-but-evade-getter
	# https://docs.python.org/3/howto/descriptor.html#properties
	# can have it named same or different
	logger = property(fset=_set_logger, doc="'logger' property to set to the class logging.Logger")






	#########################################################################################
	#################################### PROCESS CONTROL ####################################
	#########################################################################################


	# ----------------------------------------------------------------------------------------------------------------------

	def run(self) -> None:
		"""Start an ``exiftool`` process in batch mode for this instance.

		This method will issue a ``UserWarning`` if the subprocess is
		already running.  The process is by default started with the ``-G``
		and ``-n`` (print conversion disabled) as common arguments,
		which are automatically included in every command you run with
		:py:meth:`execute()`.

		However, you can override these default arguments with the
		``common_args`` parameter in the constructor.

		If it doesn't run successfully, an error will be raised, otherwise, the ``exiftool`` process has started

		If the minimum required version check fails, a RuntimeError will be raised, and exiftool is automatically terminated.

		(if you have another executable named exiftool which isn't exiftool, then you're shooting yourself in the foot as there's no error checking for that)
		"""
		if self.running:
			warnings.warn("ExifTool already running; doing nothing.", UserWarning)
			return

		# first the executable ...
		proc_args = [self._executable, ]

		# If working with a config file, it must be the first argument after the executable per: https://exiftool.org/config.html
		if self._config_file:
			proc_args.extend(["-config", self._config_file])

		# this is the required stuff for the stay_open that makes pyexiftool so great!
		proc_args.extend(["-stay_open", "True", "-@", "-"])

		# only if there are any common_args.  [] and None are skipped equally with this
		if self._common_args:
			proc_args.append("-common_args")  # add this param only if there are common_args
			proc_args.extend(self._common_args)  # add the common arguments


		# ---- set platform-specific kwargs for Popen ----
		kwargs: dict = {}

		if constants.PLATFORM_WINDOWS:
			# TODO: I don't think this code actually does anything ... I've never seen a console pop up on Windows
			# Perhaps need to specify subprocess.STARTF_USESHOWWINDOW to actually have any console pop up?
			# https://docs.python.org/3/library/subprocess.html#windows-popen-helpers
			startup_info = subprocess.STARTUPINFO()
			if not self._win_shell:
				# Adding enum 11 (SW_FORCEMINIMIZE in win32api speak) will
				# keep it from throwing up a DOS shell when it launches.
				startup_info.dwFlags |= constants.SW_FORCEMINIMIZE

			kwargs['startupinfo'] = startup_info
		else:  # pytest-cov:windows: no cover
			# assume it's linux
			kwargs['preexec_fn'] = _set_pdeathsig(signal.SIGTERM)
			# Warning: The preexec_fn parameter is not safe to use in the presence of threads in your application.
			# https://docs.python.org/3/library/subprocess.html#subprocess.Popen


		try:
			# unify both platform calls into one subprocess.Popen call
			self._process = subprocess.Popen(
				proc_args,
				stdin=subprocess.PIPE,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				encoding=self._encoding,
				**kwargs)
		except FileNotFoundError as fnfe:
			raise
		except OSError as oe:
			raise
		except ValueError as ve:
			raise
		except subprocess.CalledProcessError as cpe:
			raise
		# TODO print out more useful error messages to these different errors above

		# check error above before saying it's running
		if self._process.poll() is not None:
			# the Popen launched, then process terminated
			self._process = None  # unset it as it's now terminated
			raise RuntimeError("exiftool did not execute successfully")


		# have to set this before doing the checks below, or else execute() will fail
		self._running = True

		# get ExifTool version here and any Exiftool metadata
		# this can also verify that it is really ExifTool we ran, not some other random process
		try:
			# apparently because .execute() has code that already depends on v12.15+ functionality, this will throw a ValueError immediately with
			#   ValueError: invalid literal for int() with base 10: '${status}'
			self._ver = self._parse_ver()
		except ValueError:
			# trap the error and return it as a minimum version problem
			self.terminate()
			raise RuntimeError(f"Error retrieving Exiftool info.  Is your Exiftool version ('exiftool -ver') >= required version ('{constants.EXIFTOOL_MINIMUM_VERSION}')?")

		if self._logger: self._logger.info(f"Method 'run': Exiftool version '{self._ver}' (pid {self._process.pid}) launched with args '{proc_args}'")


		# currently not needed... if it passes -ver, the rest is OK
		"""
		# check that the minimum required version is met, if not, terminate...
		# if you run against a version which isn't supported, strange errors come up during execute()
		if not self._exiftool_version_check():
			self.terminate()
			if self._logger: self._logger.error(f"Method 'run': Exiftool version '{self._ver}' did not meet the required minimum version '{constants.EXIFTOOL_MINIMUM_VERSION}'")
			raise RuntimeError(f"exiftool version '{self._ver}' < required '{constants.EXIFTOOL_MINIMUM_VERSION}'")
		"""


	# ----------------------------------------------------------------------------------------------------------------------
	def terminate(self, timeout: int = 30, _del: bool = False) -> None:
		"""Terminate the ``exiftool`` process of this instance.

		If the subprocess isn't running, this method will throw a warning, and do nothing.
		"""
		if not self.running:
			warnings.warn("ExifTool not running; doing nothing.", UserWarning)
			# TODO, maybe add an optional parameter that says ignore_running/check/force or something which will not warn
			return

		if _del and constants.PLATFORM_WINDOWS:
			# don't cleanly exit on windows, during __del__ as it'll freeze at communicate()
			self._process.kill()
			#print("before comm", self._process.poll(), self._process)
			self._process.poll()
			# TODO freezes here on windows if subprocess zombie remains
			outs, errs = self._process.communicate()  # have to cleanup the process or else .poll() will return None
			#print("after comm")
			# TODO a bug filed with Python, or user error... this doesn't seem to work at all ... .communicate() still hangs
			# https://bugs.python.org/issue43784 ... Windows-specific issue affecting Python 3.8-3.10 (as of this time)
		else:
			try:
				"""
					On Windows, running this after __del__ freezes at communicate(), regardless of timeout
						this is possibly because the file descriptors are no longer valid or were closed at __del__

						test yourself with simple code that calls .run() and then end of script

					On Linux, this runs as is, and the process terminates properly
				"""
				self._process.communicate(input="-stay_open\nFalse\n", timeout=timeout)  # TODO these are constants which should be elsewhere defined
				self._process.kill()
			except subprocess.TimeoutExpired:  # this is new in Python 3.3 (for python 2.x, use the PyPI subprocess32 module)
				self._process.kill()
				outs, errs = self._process.communicate()
				# err handling code from https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate

		self._flag_running_false()

		# TODO log / return exit status from exiftool?
		if self._logger: self._logger.info("Method 'terminate': Exiftool terminated successfully.")





	##################################################################################
	#################################### EXECUTE* ####################################
	##################################################################################

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

		The parameters must be in ``str``, use the `encoding` property to change to
		encoding exiftool accepts.  For filenames, this should be the
		system's filesystem encoding.

		.. note:: This is considered a low-level method, and should
		   rarely be needed by application developers.
		"""
		if not self.running:
			raise RuntimeError("ExifTool instance not running.")


		# ---------- build the special params to execute ----------

		# there's a special usage of execute/ready specified in the manual which make almost ensure we are receiving the right signal back
		# from exiftool man pages:  When this number is added, -q no longer suppresses the "{ready}"
		signal_num = random.randint(100000, 999999)  # arbitrary create a 6 digit number (keep it down to save memory maybe)

		# constant special sequences when running -stay_open mode
		seq_execute = f"-execute{signal_num}\n"  # the default string is b"-execute\n"
		seq_ready = f"{{ready{signal_num}}}"  # the default string is b"{ready}"

		# these are special sequences to help with synchronization.  It will print specific text to STDERR before and after processing
		#SEQ_STDERR_PRE_FMT = "pre{}" # can have a PRE sequence too but we don't need it for syncing
		seq_err_post = f"post{signal_num}"  # default there isn't any string

		SEQ_ERR_STATUS_DELIM = "="  # this can be configured to be one or more chacters... the code below will accomodate for longer sequences: len() >= 1
		seq_err_status = "${status}"  # a special sequence, ${status} returns EXIT STATUS as per exiftool documentation - only supported on exiftool v12.10+

		# f-strings are faster than concatentation of multiple strings -- https://stackoverflow.com/questions/59180574/string-concatenation-with-vs-f-string
		cmd_text = "\n".join(params + ("-echo4", f"{SEQ_ERR_STATUS_DELIM}{seq_err_status}{SEQ_ERR_STATUS_DELIM}{seq_err_post}", seq_execute))


		# ---------- write to the pipe connected with exiftool process ----------

		self._process.stdin.write(cmd_text)
		self._process.stdin.flush()

		if self._logger: self._logger.info("Method 'execute': Command sent = {}".format(cmd_text.split('\n')[:-1]))


		# ---------- read output from exiftool process until special sequences reached ----------

		fdout = self._process.stdout.fileno()
		raw_stdout = _read_fd_endswith(fdout, seq_ready.encode(self._encoding), self._block_size).decode(self._encoding)

		# when it's ready, we can safely read all of stderr out, as the command is already done
		fderr = self._process.stderr.fileno()
		raw_stderr = _read_fd_endswith(fderr, seq_err_post.encode(self._encoding), self._block_size).decode(self._encoding)


		# ---------- parse output ----------

		# save the outputs to some variables first
		cmd_stdout = raw_stdout.strip()[:-len(seq_ready)]
		cmd_stderr = raw_stderr.strip()[:-len(seq_err_post)]  # save it in case the RuntimeError happens and output can be checked easily

		# sanity check the status code from the stderr output
		delim_len = len(SEQ_ERR_STATUS_DELIM)
		if cmd_stderr[-delim_len:] != SEQ_ERR_STATUS_DELIM:
			# exiftool is expected to dump out the status code within the delims... if it doesn't, the class is broken
			raise RuntimeError(f"Exiftool expected to return status on stderr, but got unexpected character: {cmd_stderr[-delim_len:]} != {SEQ_ERR_STATUS_DELIM}")

		# look for the previous delim (we could use regex here to do all this in one step, but it's probably overkill, and could slow down the code significantly)
		# the other simplification that can be done is that, Exiftool is expected to only return 0, 1, or 2 as per documentation
		# you could just lop the last 3 characters off... but if the return status changes in the future, then this code would break
		err_delim_1 = cmd_stderr.rfind(SEQ_ERR_STATUS_DELIM, 0, -delim_len)
		cmd_status = cmd_stderr[err_delim_1 + delim_len : -delim_len]


		# ---------- save the output to class vars for later retrieval ----------

		# lop off the actual status code from stderr
		self._last_stderr = cmd_stderr[:err_delim_1]
		self._last_stdout = cmd_stdout
		# can check .isnumeric() here, but best just to duck-type cast it
		self._last_status = int(cmd_status)



		if self._logger:
			self._logger.debug(f"Method 'execute': Reply stdout = \"{self._last_stdout}\"")
			self._logger.debug(f"Method 'execute': Reply stderr = \"{self._last_stderr}\"")
			self._logger.debug(f"Method 'execute': Reply status = {self._last_status}")


		# the standard return: just stdout
		# if you need other output, retrieve from properties
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


		"""
		params = map(os.fsencode, params)  # don't fsencode all params, leave them alone for exiftool process to manage
		# Some latin bytes won't decode to utf-8.
		# Try utf-8 and fallback to latin.
		# http://stackoverflow.com/a/5552623/1318758
		# https://github.com/jmathai/elodie/issues/127
		"""

		res_stdout = self.execute("-j", *params)
		# TODO these aren't used, if not important, comment them out
		res_err = self._last_stderr
		res_status = self._last_status


		if len(res_stdout) == 0:
			# the output from execute() can be empty under many relatively ambiguous situations
			# * command has no files it worked on
			# * a file specified or files does not exist
			# * some other type of error
			# * a command that does not return anything (like setting tags)
			#
			# There's no easy way to check which params are files, or else we have to reproduce the parser exiftool does (so it's hard to detect to raise a FileNotFoundError)

			# Returning [] could be ambugious if Exiftool changes the returned JSON structure in the future
			# Returning None is the safest as it clearly indicates that nothing came back from execute()
			return None


		res_decoded = res_stdout
		"""
		# TODO use fsdecode?
		# os.fsdecode() instead of res_stdout.decode()
		try:
			res_decoded = res_stdout
		except UnicodeDecodeError:
			res_decoded = res_stdout.decode(ENCODING_LATIN1)
		"""
		# TODO res_decoded can be invalid json (test this) if `-w` flag is specified in common_args
		# which will return something like
		# image files read
		# output files created

		# res_decoded is also not valid if you do metadata manipulation without returning anything
		if self._no_output:
			print(res_decoded)
			# TODO: test why is this not returning anything from this function?? what if we are SETTING something and not GETTING?
		else:
			# TODO: if len(res_decoded) == 0, then there's obviously an error here
			#print(res_decoded)
			return json.loads(res_decoded)

		# TODO , return_tuple will also beautify stderr and output status as well


	#########################################################################################
	#################################### PRIVATE METHODS ####################################
	#########################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	def _flag_running_false(self) -> None:
		""" private method that resets the "running" state
			It used to be that there was only self._running to unset, but now it's a trio of variables

			This method makes it less likely a maintainer will leave off a variable if other ones are added in the future
		"""
		self._process = None  # don't delete, just leave as None
		self._ver = None  # unset the version
		self._running = False

		# as an FYI, as per the last_* properties, they are intentionally not cleared when process closes


	# ----------------------------------------------------------------------------------------------------------------------
	def _parse_ver(self):
		""" private method to run exiftool -ver
			and parse out the information
		"""
		if not self.running:
			raise RuntimeError("ExifTool instance not running.")


		# -ver is just the version
		# -v gives you more info (perl version, platform, libraries) but isn't helpful for this library
		# -v2 gives you even more, but it's less useful at that point
		return self.execute("-ver").strip()

	# ----------------------------------------------------------------------------------------------------------------------
	"""
	def _exiftool_version_check(self) -> bool:
		"" " private method to check the minimum required version of ExifTool

		returns false if the version check fails
		returns true if it's OK

		"" "

		# parse (major, minor) with integers... so far Exiftool versions are all ##.## with no exception
		# this isn't entirely tested... possibly a version with more "." or something might break this parsing
		arr: List = self._ver.split(".", 1)  # split to (major).(whatever)

		version_nums: List = []
		try:
			for v in arr:
				res.append(int(v))
		except ValueError:
			raise ValueError(f"Error parsing ExifTool version for version check: '{self._ver}'")

		if len(version_nums) != 2:
			raise ValueError(f"Expected Major.Minor len()==2, got: {version_nums}")

		curr_major, curr_minor = version_nums


		# same logic above except on one line
		req_major, req_minor = [int(x) for x in constants.EXIFTOOL_MINIMUM_VERSION.split(".", 1)]

		if curr_major > req_major:
			# major version is bigger
			return True
		elif curr_major < req_major:
			# major version is smaller
			return False
		elif curr_minor >= req_minor:
			# major version is equal
			# current minor is equal or better
			return True
		else:
			# anything else is False
			return False
	"""

	# ----------------------------------------------------------------------------------------------------------------------
