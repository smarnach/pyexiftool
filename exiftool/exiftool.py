# -*- coding: utf-8 -*-
#
# This file is part of PyExifTool.
#
# PyExifTool <http://github.com/sylikc/pyexiftool>
#
# Copyright 2019-2023 Kevin M (sylikc)
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
This submodule contains the core ``ExifTool`` class of PyExifTool

.. note::
	:py:class:`exiftool.helper.ExifTool` class of this submodule is available in the ``exiftool`` namespace as :py:class:`exiftool.ExifTool`

"""

# ---------- standard Python imports ----------
import select
import subprocess
import os
import shutil
from pathlib import Path  # requires Python 3.4+
import random
import locale
import warnings
import json  # NOTE: to use other json libraries (simplejson/ujson/orjson/...), see :py:meth:`set_json_loads()`

# for the pdeathsig
import signal
import ctypes



# ---------- Typing Imports ----------
# for static analysis / type checking - Python 3.5+
from collections.abc import Callable
from typing import Optional, List, Union



# ---------- Library Package Imports ----------

from . import constants
from .exceptions import ExifToolVersionError, ExifToolRunning, ExifToolNotRunning, ExifToolOutputEmptyError, ExifToolJSONInvalidError


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
		return None  # pragma: no cover


# ======================================================================================================================

def _get_buffer_end(buffer_list: List[bytes], bytes_needed: int) -> bytes:
	""" Given a list of bytes objects, return the equivalent of
		b"".join(buffer_list)[-bytes_needed:]
		but without having to concatenate the entire list.
	"""
	if bytes_needed < 1:
		return b""  # pragma: no cover

	buf_chunks = []
	for buf in reversed(buffer_list):
		buf_tail = buf[-bytes_needed:]
		buf_chunks.append(buf_tail)
		bytes_needed -= len(buf_tail)
		if bytes_needed <= 0:
			break

	buf_tail_joined = b"".join(reversed(buf_chunks))
	return buf_tail_joined


def _read_fd_endswith(fd, b_endswith: bytes, block_size: int) -> bytes:
	""" read an fd and keep reading until it endswith the seq_ends

		this allows a consolidated read function that is platform indepdent

		if you're not careful, on windows, this will block
	"""
	output_list: List[bytes] = []

	# if we're only looking at the last few bytes, make it meaningful.  4 is max size of \r\n? (or 2)
	# this value can be bigger to capture more bytes at the "tail" of the read, but if it's too small, the whitespace might miss the detection
	endswith_count = len(b_endswith) + 4

	# I believe doing a splice, then a strip is more efficient in memory hence the original code did it this way.
	# need to benchmark to see if in large strings, strip()[-endswithcount:] is more expensive or not
	while not _get_buffer_end(output_list, endswith_count).strip().endswith(b_endswith):
		if constants.PLATFORM_WINDOWS:
			# windows does not support select() for anything except sockets
			# https://docs.python.org/3.7/library/select.html
			output_list.append(os.read(fd, block_size))
		else:  # pytest-cov:windows: no cover
			# this does NOT work on windows... and it may not work on other systems... in that case, put more things to use the original code above
			inputready, outputready, exceptready = select.select([fd], [], [])
			for i in inputready:
				if i == fd:
					output_list.append(os.read(fd, block_size))

	return b"".join(output_list)






# ======================================================================================================================

class ExifTool(object):
	"""Run the `exiftool` command-line tool and communicate with it.

	Use ``common_args`` to enable/disable print conversion by specifying/omitting ``-n``, respectively.
	This determines whether exiftool should perform print conversion,
	which prints values in a human-readable way but
	may be slower. If print conversion is enabled, appending ``#`` to a tag
	name disables the print conversion for this particular tag.
	See `Exiftool print conversion FAQ`_ for more details.

	.. _Exiftool print conversion FAQ: https://exiftool.org/faq.html#Q6


	Some methods of this class are only available after calling
	:py:meth:`run()`, which will actually launch the *exiftool* subprocess.
	To avoid leaving the subprocess running, make sure to call
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

	.. warning::
		Note that options and parameters are not checked.  There is no error handling or validation of options passed to *exiftool*.

		Nonsensical options are mostly silently ignored by exiftool, so there's not
		much that can be done in that regard.  You should avoid passing
		non-existent files to any of the methods, since this will lead
		to undefined behaviour.

	"""

	##############################################################################
	#################################### INIT ####################################
	##############################################################################

	# ----------------------------------------------------------------------------------------------------------------------

	def __init__(self,
	  executable: Optional[str] = None,
	  common_args: Optional[List[str]] = ["-G", "-n"],
	  win_shell: bool = False,
	  config_file: Optional[Union[str, Path]] = None,
	  encoding: Optional[str] = None,
	  logger = None) -> None:
		"""

		:param executable: Specify file name of the *exiftool* executable if it is in your ``PATH``.  Otherwise, specify the full path to the ``exiftool`` executable.

			Passed directly into :py:attr:`executable` property.

			.. note::
				The default value :py:attr:`exiftool.constants.DEFAULT_EXECUTABLE` will only work if the executable is in your ``PATH``.

		:type executable: str, or None to use default


		:param common_args:
			Pass in additional parameters for the stay-open instance of exiftool.

			Defaults to ``["-G", "-n"]`` as this is the most common use case.

			* ``-G`` (groupName level 1 enabled) separates the output with *groupName:tag* to disambiguate same-named tags under different groups.
			* ``-n`` (print conversion disabled) improves the speed and consistency of output, and is more machine-parsable

			Passed directly into :py:attr:`common_args` property.


			.. note::
				Depending on your use case, there may be other useful grouping levels and options.  Search `Phil Harvey's exiftool documentation`_ for **groupNames** and **groupHeadings** to get more info.



			.. _`Phil Harvey's exiftool documentation`: https://exiftool.org/exiftool_pod.html

		:type common_args: list of str, or None.

		:param bool win_shell: (Windows only) Minimizes the exiftool process.

			.. note::
				This parameter may be deprecated in the future

		:param config_file:
			File path to ``-config`` parameter when starting exiftool process.

			Passed directly into :py:attr:`config_file` property.
		:type config_file: str, Path, or None

		:param encoding: Specify encoding to be used when communicating with
			exiftool process.  By default, will use ``locale.getpreferredencoding()``

			Passed directly into :py:attr:`encoding` property.

		:param logger: Set a custom logger to log status and debug messages to.

			Passed directly into :py:attr:`logger` property.
		"""

		# --- default settings / declare member variables ---
		self._running: bool = False  # is it running?
		"""A Boolean value indicating whether this instance is currently
		associated with a running subprocess."""
		self._win_shell: bool = win_shell  # do you want to see the shell on Windows?

		self._process = None  # this is set to the process to interact with when _running=True
		self._ver: Optional[str] = None  # this is set to be the exiftool -v -ver when running

		self._last_stdout: Optional[str] = None  # previous output
		self._last_stderr: Optional[str] = None  # previous stderr
		self._last_status: Optional[int] = None  # previous exit status from exiftool (look up EXIT STATUS in exiftool documentation for more information)

		self._block_size: int = constants.DEFAULT_BLOCK_SIZE  # set to default block size


		# these are set via properties
		self._executable: Union[str, Path] = constants.DEFAULT_EXECUTABLE  # executable absolute path (default set to just the executable name, so it can't be None)
		self._config_file: Optional[str] = None  # config file that can only be set when exiftool is not running
		self._common_args: Optional[List[str]] = None
		self._logger = None
		self._encoding: Optional[str] = None
		self._json_loads: Callable = json.loads  # variable points to the actual callable method
		self._json_loads_kwargs: dict = {}  # default optional params to pass into json.loads() call



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
	def executable(self) -> Union[str, Path]:
		"""
		Path to *exiftool* executable.

		:getter: Returns current exiftool path
		:setter: Specify just the executable name, or an absolute path to the executable.
			If path given is not absolute, searches environment ``PATH``.

			.. note::
				Setting is only available when exiftool process is not running.

		:raises ExifToolRunning: If attempting to set while running (:py:attr:`running` == True)
		:type: str, Path
		"""
		return self._executable

	@executable.setter
	def executable(self, new_executable: Union[str, Path]) -> None:
		# cannot set executable when process is running
		if self.running:
			raise ExifToolRunning("Cannot set new executable")

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
		self._executable = str(abs_path)

		if self._logger: self._logger.info(f"Property 'executable': set to \"{abs_path}\"")


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def encoding(self) -> Optional[str]:
		"""
		Encoding of Popen() communication with *exiftool* process.

		:getter: Returns current encoding setting

		:setter: Set a new encoding.

			* If *new_encoding* is None, will detect it from ``locale.getpreferredencoding(do_setlocale=False)`` (do_setlocale is set to False as not to affect the caller).
			* Default to ``utf-8`` if nothing is returned by ``getpreferredencoding``

			.. warning::
				Property setter does NOT validate the encoding for validity.  It is passed verbatim into subprocess.Popen()

			.. note::
				Setting is only available when exiftool process is not running.

		:raises ExifToolRunning: If attempting to set while running (:py:attr:`running` == True)

		"""
		return self._encoding

	@encoding.setter
	def encoding(self, new_encoding: Optional[str]) -> None:
		# cannot set encoding when process is running
		if self.running:
			raise ExifToolRunning("Cannot set new encoding")

		# auto-detect system specific
		self._encoding = new_encoding or (locale.getpreferredencoding(do_setlocale=False) or ENCODING_UTF8)


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def block_size(self) -> int:
		"""
		Block size for communicating with *exiftool* subprocess.  Used when reading from the I/O pipe.

		:getter: Returns current block size

		:setter: Set a new block_size.  Does basic error checking to make sure > 0.

		:raises ValueError: If new block size is invalid

		:type: int
		"""
		return self._block_size

	@block_size.setter
	def block_size(self, new_block_size: int) -> None:
		if new_block_size <= 0:
			raise ValueError("Block Size doesn't make sense to be <= 0")

		self._block_size = new_block_size

		if self._logger: self._logger.info(f"Property 'block_size': set to \"{new_block_size}\"")


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def common_args(self) -> Optional[List[str]]:
		"""
		Common Arguments executed with every command passed to *exiftool* subprocess

		This is the parameter `-common_args`_ that is passed when the *exiftool* process is STARTED

		Read `Phil Harvey's ExifTool documentation`_ to get further information on what options are available / how to use them.

		.. _-common_args: https://exiftool.org/exiftool_pod.html#Advanced-options
		.. _Phil Harvey's ExifTool documentation: https://exiftool.org/exiftool_pod.html

		:getter: Returns current common_args list

		:setter: If ``None`` is passed in, sets common_args to ``[]``.  Otherwise, sets the given list without any validation.

			.. warning::
				No validation is done on the arguments list.  It is passed verbatim to *exiftool*.  Invalid options or combinations may result in undefined behavior.

			.. note::
				Setting is only available when exiftool process is not running.

		:raises ExifToolRunning: If attempting to set while running (:py:attr:`running` == True)
		:raises TypeError: If setting is not a list

		:type: list[str], None
		"""
		return self._common_args

	@common_args.setter
	def common_args(self, new_args: Optional[List[str]]) -> None:

		if self.running:
			raise ExifToolRunning("Cannot set new common_args")

		if new_args is None:
			self._common_args = []
		elif isinstance(new_args, list):
			# default parameters to exiftool
			# -n = disable print conversion (speedup)
			self._common_args = new_args
		else:
			raise TypeError("common_args not a list of strings")

		if self._logger: self._logger.info(f"Property 'common_args': set to \"{self._common_args}\"")


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def config_file(self) -> Optional[Union[str, Path]]:
		"""
		Path to config file.

		See `ExifTool documentation for -config`_ for more details.


		:getter: Returns current config file path, or None if not set

		:setter: File existence is checked when setting parameter

			* Set to ``None`` to disable the ``-config`` parameter when starting *exiftool*
			* Set to ``""`` has special meaning and disables loading of the default config file.  See `ExifTool documentation for -config`_ for more info.

			.. note::
				Currently file is checked for existence when setting.  It is not checked when starting process.

		:raises ExifToolRunning: If attempting to set while running (:py:attr:`running` == True)

		:type: str, Path, None

		.. _ExifTool documentation for -config: https://exiftool.org/exiftool_pod.html#Advanced-options
		"""
		return self._config_file

	@config_file.setter
	def config_file(self, new_config_file: Optional[Union[str, Path]]) -> None:
		if self.running:
			raise ExifToolRunning("Cannot set a new config_file")

		if new_config_file is None:
			self._config_file = None
		elif new_config_file == "":
			# this is VALID usage of -config parameter
			# As per exiftool documentation:  Loading of the default config file may be disabled by setting CFGFILE to an empty string (ie. "")
			self._config_file = ""
		elif not Path(new_config_file).exists():
			raise FileNotFoundError("The config file could not be found")
		else:
			self._config_file = str(new_config_file)

		if self._logger: self._logger.info(f"Property 'config_file': set to \"{self._config_file}\"")



	##############################################################################################
	#################################### PROPERTIES Read only ####################################
	##############################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def running(self) -> bool:
		"""
		Read-only property which indicates whether the *exiftool* subprocess is running or not.

		:getter: Returns current running state

			.. note::
				This checks to make sure the process is still alive.

				If the process has died since last `running` detection, this property
				will detect the state change and reset the status accordingly.
		"""
		if self._running:
			# check if the process is actually alive
			if self._process.poll() is not None:
				# process died
				warnings.warn("ExifTool process was previously running but died")
				self._flag_running_false()

				if self._logger: self._logger.warning("Property 'running': ExifTool process was previously running but died")

		return self._running


	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def version(self) -> str:
		"""
		Read-only property which is the string returned by ``exiftool -ver``

		The *-ver* command is ran once at process startup and cached.

		:getter: Returns cached output of ``exiftool -ver``

		:raises ExifToolNotRunning: If attempting to read while not running (:py:attr:`running` == False)
		"""

		if not self.running:
			raise ExifToolNotRunning("Can't get ExifTool version")

		return self._ver

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def last_stdout(self) -> Optional[Union[str, bytes]]:
		"""
		``STDOUT`` for most recent result from execute()

		.. note::
			The return type can be either str or bytes.

			If the most recent call to execute() ``raw_bytes=True``, then this will return ``bytes``.  Otherwise this will be ``str``.

		.. note::
			This property can be read at any time, and is not dependent on running state of ExifTool.

			It is INTENTIONALLY *NOT* CLEARED on exiftool termination, to allow
			for executing a command and terminating, but still having the result available.
		"""
		return self._last_stdout

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def last_stderr(self) -> Optional[Union[str, bytes]]:
		"""
		``STDERR`` for most recent result from execute()

		.. note::
			The return type can be either ``str`` or ``bytes``.

			If the most recent call to execute() ``raw_bytes=True``, then this will return ``bytes``.  Otherwise this will be ``str``.

		.. note::
			This property can be read at any time, and is not dependent on running state of ExifTool.

			It is INTENTIONALLY *NOT* CLEARED on exiftool termination, to allow
			for executing a command and terminating, but still having the result available.
		"""
		return self._last_stderr

	# ----------------------------------------------------------------------------------------------------------------------
	@property
	def last_status(self) -> Optional[int]:
		"""
		``Exit Status Code`` for most recent result from execute()

		.. note::
			This property can be read at any time, and is not dependent on running state of ExifTool.

			It is INTENTIONALLY *NOT* CLEARED on exiftool termination, to allow
			for executing a command and terminating, but still having the result available.
		"""
		return self._last_status




	###############################################################################################
	#################################### PROPERTIES Write only ####################################
	###############################################################################################

	# ----------------------------------------------------------------------------------------------------------------------
	def _set_logger(self, new_logger) -> None:
		""" set a new user-created logging.Logger object
			can be set at any time to start logging.

			Set to None at any time to stop logging.
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
		except AttributeError:
			check = False

		if not check:
			raise TypeError("logger needs to implement methods (info,warning,error,critical,exception)")

		self._logger = new_logger

	# have to run this at the class level to create a special write-only property
	# https://stackoverflow.com/questions/17576009/python-class-property-use-setter-but-evade-getter
	# https://docs.python.org/3/howto/descriptor.html#properties
	# can have it named same or different
	logger = property(fset=_set_logger, doc="""Write-only property to set the class of logging.Logger""")
	"""
	Write-only property to set the class of logging.Logger

	If this is set, then status messages will log out to the given class.

	.. note::
		This can be set and unset (set to ``None``) at any time, regardless of whether the subprocess is running (:py:attr:`running` == True) or not.

	:setter: Specify an object to log to.  The class is not checked, but validation is done to ensure the object has callable methods ``info``, ``warning``, ``error``, ``critical``, ``exception``.

	:raises AttributeError: If object does not contain one or more of the required methods.
	:raises TypeError: If object contains those attributes, but one or more are non-callable methods.

	:type: Object
	"""

	#########################################################################################
	##################################### SETTER METHODS ####################################
	#########################################################################################


	# ----------------------------------------------------------------------------------------------------------------------
	def set_json_loads(self, json_loads, **kwargs) -> None:
		"""
		**Advanced**: Override default built-in ``json.loads()`` method.  The method is only used once in :py:meth:`execute_json`

		This allows using a different json string parser.

		(Alternate json libraries typically provide faster speed than the
		built-in implementation, more supported features, and/or different behavior.)

		Examples of json libraries: `orjson`_, `rapidjson`_, `ujson`_, ...

		.. note::
			This method is designed to be called the same way you would expect to call the provided ``json_loads`` method.

			Include any ``kwargs`` you would in the call.

			For example, to pass additional arguments to ``json.loads()``: ``set_json_loads(json.loads, parse_float=str)``

		.. note::
			This can be set at any time, regardless of whether the subprocess is running (:py:attr:`running` == True) or not.

		.. warning::
			This setter does not check whether the method provided actually parses json.  Undefined behavior or crashes may occur if used incorrectly

			This is **advanced configuration** for specific use cases only.

			For an example use case, see the :ref:`FAQ <set_json_loads faq>`

		:param json_loads: A callable method to replace built-in ``json.loads`` used in :py:meth:`execute_json`

		:type json_loads: callable

		:param kwargs: Parameters passed to the ``json_loads`` method call

		:raises TypeError: If ``json_loads`` is not callable


		.. _orjson: https://pypi.org/project/orjson/
		.. _rapidjson: https://pypi.org/project/python-rapidjson/
		.. _ujson: https://pypi.org/project/ujson/
		"""
		if not callable(json_loads):
			# not a callable method
			raise TypeError

		self._json_loads = json_loads
		self._json_loads_kwargs = kwargs




	#########################################################################################
	#################################### PROCESS CONTROL ####################################
	#########################################################################################


	# ----------------------------------------------------------------------------------------------------------------------

	def run(self) -> None:
		"""Start an *exiftool* subprocess in batch mode.

		This method will issue a ``UserWarning`` if the subprocess is
		already running (:py:attr:`running` == True).  The process is started with :py:attr:`common_args` as common arguments,
		which are automatically included in every command you run with :py:meth:`execute()`.

		You can override these default arguments with the
		``common_args`` parameter in the constructor or setting :py:attr:`common_args` before caaling :py:meth:`run()`.

		.. note::
			If you have another executable named *exiftool* which isn't Phil Harvey's ExifTool, then you're shooting yourself in the foot as there's no error checking for that

		:raises FileNotFoundError: If *exiftool* is no longer found.  Re-raised from subprocess.Popen()
		:raises OSError: Re-raised from subprocess.Popen()
		:raises ValueError: Re-raised from subprocess.Popen()
		:raises subproccess.CalledProcessError: Re-raised from subprocess.Popen()
		:raises RuntimeError: Popen() launched process but it died right away
		:raises ExifToolVersionError: :py:attr:`exiftool.constants.EXIFTOOL_MINIMUM_VERSION` not met.  ExifTool process will be automatically terminated.
		"""
		if self.running:
			warnings.warn("ExifTool already running; doing nothing.", UserWarning)
			return

		# first the executable ...
		# TODO should we check the executable for existence here?
		proc_args = [self._executable, ]

		# If working with a config file, it must be the first argument after the executable per: https://exiftool.org/config.html
		if self._config_file is not None:
			# must check explicitly for None, as "" is valid
			# TODO check that the config file exists here?
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

			kwargs["startupinfo"] = startup_info
		else:  # pytest-cov:windows: no cover
			# assume it's linux
			kwargs["preexec_fn"] = _set_pdeathsig(signal.SIGTERM)
			# Warning: The preexec_fn parameter is not safe to use in the presence of threads in your application.
			# https://docs.python.org/3/library/subprocess.html#subprocess.Popen


		try:
			# NOTE: the encoding= parameter was removed from the Popen() call to support
			# using bytes in the actual communication with exiftool process.
			# Due to the way the code is written, ExifTool only uses stdin.write which would need to be in bytes.
			# The reading is _NOT_ using subprocess.communicate().  This class reads raw bytes using os.read()
			# Therefore, by switching off the encoding= in Popen(), we can support both bytes and str at the
			# same time.  (This change was to support https://github.com/sylikc/pyexiftool/issues/47)

			# unify both platform calls into one subprocess.Popen call
			self._process = subprocess.Popen(
				proc_args,
				stdin=subprocess.PIPE,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				**kwargs)
		except FileNotFoundError:
			raise
		except OSError:
			raise
		except ValueError:
			raise
		except subprocess.CalledProcessError:
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
			# apparently because .execute() has code that already depends on v12.15+ functionality,
			# _parse_ver() will throw a ValueError immediately with:
			#   ValueError: invalid literal for int() with base 10: '${status}'
			self._ver = self._parse_ver()
		except ValueError:
			# trap the error and return it as a minimum version problem
			self.terminate()
			raise ExifToolVersionError(f"Error retrieving Exiftool info.  Is your Exiftool version ('exiftool -ver') >= required version ('{constants.EXIFTOOL_MINIMUM_VERSION}')?")

		if self._logger: self._logger.info(f"Method 'run': Exiftool version '{self._ver}' (pid {self._process.pid}) launched with args '{proc_args}'")


		# currently not needed... if it passes -ver check, the rest is OK
		# may use in the future again if another version feature is needed but the -ver check passes
		"""
		# check that the minimum required version is met, if not, terminate...
		# if you run against a version which isn't supported, strange errors come up during execute()
		if not self._exiftool_version_check():
			self.terminate()
			if self._logger: self._logger.error(f"Method 'run': Exiftool version '{self._ver}' did not meet the required minimum version '{constants.EXIFTOOL_MINIMUM_VERSION}'")
			raise ExifToolVersionError(f"exiftool version '{self._ver}' < required '{constants.EXIFTOOL_MINIMUM_VERSION}'")
		"""


	# ----------------------------------------------------------------------------------------------------------------------
	def terminate(self, timeout: int = 30, _del: bool = False) -> None:
		"""Terminate the *exiftool* subprocess.

		If the subprocess isn't running, this method will throw a warning, and do nothing.

		.. note::
			There is a bug in CPython 3.8+ on Windows where terminate() does not work during ``__del__()``

			See CPython issue `starting a thread in __del__ hangs at interpreter shutdown`_ for more info.

		.. _starting a thread in __del__ hangs at interpreter shutdown: https://github.com/python/cpython/issues/87950
		"""
		if not self.running:
			warnings.warn("ExifTool not running; doing nothing.", UserWarning)
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
						see the bug filed above for details

					On Linux, this runs as is, and the process terminates properly
				"""
				self._process.communicate(input=b"-stay_open\nFalse\n", timeout=timeout)  # this is a constant sequence specified by PH's exiftool
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
	def execute(self, *params: Union[str, bytes], raw_bytes: bool = False) -> Union[str, bytes]:
		"""Execute the given batch of parameters with *exiftool*.

		This method accepts any number of parameters and sends them to
		the attached ``exiftool`` subprocess.  The process must be
		running, otherwise :py:exc:`exiftool.exceptions.ExifToolNotRunning` is raised.  The final
		``-execute`` necessary to actually run the batch is appended
		automatically; see the documentation of :py:meth:`run()` for
		the common options.  The ``exiftool`` output is read up to the
		end-of-output sentinel and returned as a ``str`` decoded
		based on the currently set :py:attr:`encoding`,
		excluding the sentinel.

		The parameters must be of type ``str`` or ``bytes``.
		``str`` parameters are encoded to bytes automatically using the :py:attr:`encoding` property.
		For filenames, this should be the system's filesystem encoding.
		``bytes`` parameters are untouched and passed directly to ``exiftool``.

		.. note::
			This is the core method to interface with the ``exiftool`` subprocess.

			No processing is done on the input or output.

		:param params: One or more parameters to send to the ``exiftool`` subprocess.

			Typically passed in via `Unpacking Argument Lists`_

			.. note::
				The parameters to this function must be type ``str`` or ``bytes``.

		:type params: one or more string/bytes parameters

		:param raw_bytes: If True, returns bytes.  Default behavior returns a str


		:return:
			* STDOUT is returned by the method call, and is also set in :py:attr:`last_stdout`
			* STDERR is set in :py:attr:`last_stderr`
			* Exit Status of the command is set in :py:attr:`last_status`

		:raises ExifToolNotRunning: If attempting to execute when not running (:py:attr:`running` == False)
		:raises ExifToolVersionError: If unexpected text was returned from the command while parsing out the sentinels
		:raises UnicodeDecodeError: If the :py:attr:`encoding` is not specified properly, it may be possible for ``.decode()`` method to raise this error
		:raises TypeError: If ``params`` argument is not ``str`` or ``bytes``


		.. _Unpacking Argument Lists: https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists
		"""
		if not self.running:
			raise ExifToolNotRunning("Cannot execute()")


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


		# ---------- build the params list and encode the params to bytes, if necessary ----------
		cmd_params: List[bytes] = []

		# this is necessary as the encoding parameter of Popen() is not specified.  We manually encode as per the .encoding() parameter
		for p in params:
			# we use isinstance() over type() not only for subclass, but
			# according to https://switowski.com/blog/type-vs-isinstance
			# isinstance() is 40% faster than type()
			if isinstance(p, bytes):
				# no conversion needed, pass in raw (caller has already encoded)
				cmd_params.append(p)
			elif isinstance(p, str):
				# conversion needed, encode based on specified encoding
				cmd_params.append(p.encode(self._encoding))
			else:
				# technically at this point we could support any object and call str()
				# but leave this up to an extended class like ExifToolHelper()
				raise TypeError(f"ERROR: Parameter was not bytes/str: {type(p)} => {p}")

		# f-strings are faster than concatentation of multiple strings -- https://stackoverflow.com/questions/59180574/string-concatenation-with-vs-f-string
		cmd_params.extend(
			(b"-echo4",
			f"{SEQ_ERR_STATUS_DELIM}{seq_err_status}{SEQ_ERR_STATUS_DELIM}{seq_err_post}".encode(self._encoding),
			seq_execute.encode(self._encoding))
		)

		cmd_bytes = b"\n".join(cmd_params)


		# ---------- write to the pipe connected with exiftool process ----------

		self._process.stdin.write(cmd_bytes)
		self._process.stdin.flush()

		if self._logger: self._logger.info("Method 'execute': Command sent = {}".format(cmd_params[:-1]))  # logs without the -execute (it would confuse people to include that)


		# ---------- read output from exiftool process until special sequences reached ----------

		# NOTE:
		#
		# while subprocess recommends: "Use communicate() rather than .stdin.write, .stdout.read or .stderr.read to avoid deadlocks due to any of the other OS pipe buffers filling up and blocking the child process."
		#
		# this raw reading is used instead of Popen.communicate() due to the note:
		# https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
		#
		# "The data read is buffered in memory, so do not use this method if the data size is large or unlimited."
		#
		# The data that comes back from exiftool falls into this, and so unbuffered reads are done with os.read()

		fdout = self._process.stdout.fileno()
		raw_stdout = _read_fd_endswith(fdout, seq_ready.encode(self._encoding), self._block_size)

		# when it's ready, we can safely read all of stderr out, as the command is already done
		fderr = self._process.stderr.fileno()
		raw_stderr = _read_fd_endswith(fderr, seq_err_post.encode(self._encoding), self._block_size)


		if not raw_bytes:
			# decode if not returning bytes
			raw_stdout = raw_stdout.decode(self._encoding)
			raw_stderr = raw_stderr.decode(self._encoding)


		# ---------- parse output ----------

		# save the outputs to some variables first
		cmd_stdout = raw_stdout.strip()[:-len(seq_ready)]
		cmd_stderr = raw_stderr.strip()[:-len(seq_err_post)]  # save it in case the error below happens and output can be checked easily


		# if raw_bytes is True, the check has to become bytes rather than str
		err_status_delim = SEQ_ERR_STATUS_DELIM if not raw_bytes else SEQ_ERR_STATUS_DELIM.encode(self._encoding)


		# sanity check the status code from the stderr output
		delim_len = len(err_status_delim)
		if cmd_stderr[-delim_len:] != err_status_delim:
			# exiftool is expected to dump out the status code within the delims... if it doesn't, the class doesn't match expected exiftool output for current version
			raise ExifToolVersionError(f"Exiftool expected to return status on stderr, but got unexpected character: {cmd_stderr[-delim_len:]} != {err_status_delim}")

		# look for the previous delim (we could use regex here to do all this in one step, but it's probably overkill, and could slow down the code significantly)
		# the other simplification that can be done is that, as of this writing: Exiftool is expected to only return 0, 1, or 2 as per documentation
		# you could just lop the last 3 characters off... but if the return status changes in the future, then this code would break
		err_delim_1 = cmd_stderr.rfind(err_status_delim, 0, -delim_len)
		cmd_status = cmd_stderr[err_delim_1 + delim_len : -delim_len]


		# ---------- save the output to class vars for later retrieval ----------

		# lop off the actual status code from stderr
		self._last_stderr = cmd_stderr[:err_delim_1]
		self._last_stdout = cmd_stdout
		# can check .isnumeric() here, but best just to duck-type cast it
		self._last_status = int(cmd_status)



		if self._logger:
			self._logger.debug(f"{self.__class__.__name__}.execute: IN  params = {params}")
			self._logger.debug(f"{self.__class__.__name__}.execute: OUT stdout = \"{self._last_stdout}\"")
			self._logger.debug(f"{self.__class__.__name__}.execute: OUT stderr = \"{self._last_stderr}\"")
			self._logger.debug(f"{self.__class__.__name__}.execute: OUT status = {self._last_status}")


		# the standard return: just stdout
		# if you need other output, retrieve from properties
		return self._last_stdout



	# ----------------------------------------------------------------------------------------------------------------------
	def execute_json(self, *params: Union[str, bytes]) -> List:
		"""Execute the given batch of parameters and parse the JSON output.

		This method is similar to :py:meth:`execute()`.  It
		automatically adds the parameter ``-j`` to request JSON output
		from ``exiftool`` and parses the output.

		The return value is
		a list of dictionaries, mapping tag names to the corresponding
		values.  All keys are strings.
		The values can have multiple types.  Each dictionary contains the
		name of the file it corresponds to in the key ``"SourceFile"``.

		.. note::
			By default, the tag names include the group name in the format <group>:<tag> (if using the ``-G`` option).

			You can adjust the output structure with various *exiftool* options.

		.. warning::
			This method does not verify the exit status code returned by *exiftool*.  That is left up to the caller.

			This will mimic exiftool's default method of operation "continue on error" and "best attempt" to complete commands given.

			If you want automated error checking, use :py:class:`exiftool.ExifToolHelper`

		:param params: One or more parameters to send to the ``exiftool`` subprocess.

			Typically passed in via `Unpacking Argument Lists`_

			.. note::
				The parameters to this function must be type ``str`` or ``bytes``.

		:type params: one or more string/bytes parameters

		:return: Valid JSON parsed into a Python list of dicts
		:raises ExifToolOutputEmptyError: If *exiftool* did not return any STDOUT

			.. note::
				This is not necessarily an *exiftool* error, but rather a programmer error.

				For example, setting tags can cause this behavior.

				If you are executing a command and expect no output, use :py:meth:`execute()` instead.

		:raises ExifToolJSONInvalidError: If *exiftool* returned STDOUT which is invalid JSON.

			.. note::
				This is not necessarily an *exiftool* error, but rather a programmer error.

				For example, ``-w`` can cause this behavior.

				If you are executing a command and expect non-JSON output, use :py:meth:`execute()` instead.


		.. _Unpacking Argument Lists: https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists
		"""

		result = self.execute("-j", *params)  # stdout

		# NOTE: I have decided NOT to check status code
		# There are quite a few use cases where it's desirable to have continue-on-error behavior,
		# as that is exiftool's default mode of operation.  exiftool normally just does what it can
		# and tells you that it did all this and that, but some files didn't process.  In this case
		# exit code is non-zero, but exiftool did SOMETHING.  I leave it up to the caller to figure
		# out what was done or not done.


		if len(result) == 0:
			# the output from execute() can be empty under many relatively ambiguous situations
			# * command has no files it worked on
			# * a file specified or files does not exist
			# * some other type of error
			# * a command that does not return anything (like metadata manipulation/setting tags)
			#
			# There's no easy way to check which params are files, or else we have to reproduce the parser exiftool does (so it's hard to detect to raise a FileNotFoundError)

			# Returning [] could be ambiguous if Exiftool changes the returned JSON structure in the future
			# Returning None was preferred, because it's the safest as it clearly indicates that nothing came back from execute(), but it means execute_json() doesn't always return JSON
			# Raising an error is the current solution, as that clearly indicates that you used execute_json() expecting output, but got nothing
			raise ExifToolOutputEmptyError(self._last_status, self._last_stdout, self._last_stderr, params)


		try:
			parsed = self._json_loads(result, **self._json_loads_kwargs)
		except ValueError as e:
			# most known JSON libraries return ValueError or a subclass.
			# built-in json.JSONDecodeError is a subclass of ValueError -- https://docs.python.org/3/library/json.html#json.JSONDecodeError

			# if `-w` flag is specified in common_args or params, stdout will not be JSON parseable
			#
			# which will return something like:
			#   x image files read
			#   x output files created

			# the user is expected to know this ahead of time, and if -w exists in common_args or as a param, this error will be thrown

			# explicit chaining https://www.python.org/dev/peps/pep-3134/
			raise ExifToolJSONInvalidError(self._last_status, self._last_stdout, self._last_stderr, params) from e

		return parsed


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
			raise ExifToolNotRunning("Cannot get version")


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
