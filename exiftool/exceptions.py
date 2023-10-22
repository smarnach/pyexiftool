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

This submodule holds all of the custom exceptions which can be raised by PyExifTool

"""


########################################################
#################### Base Exception ####################
########################################################


class ExifToolException(Exception):
	"""
	Generic Base class for all ExifTool error classes
	"""


#############################################################
#################### Process State Error ####################
#############################################################


class ExifToolProcessStateError(ExifToolException):
	"""
	Base class for all errors related to the invalid state of `exiftool` subprocess
	"""


class ExifToolRunning(ExifToolProcessStateError):
	"""
	ExifTool is already running
	"""
	def __init__(self, message: str):
		super().__init__(f"ExifTool instance is running: {message}")


class ExifToolNotRunning(ExifToolProcessStateError):
	"""
	ExifTool is not running
	"""
	def __init__(self, message: str):
		super().__init__(f"ExifTool instance not running: {message}")


###########################################################
#################### Execute Exception ####################
###########################################################

# all of these exceptions are related to something regarding execute

class ExifToolExecuteException(ExifToolException):
	"""
	This is the base exception class for all execute() associated errors.

	This exception is never returned directly from any method, but provides common interface for subclassed errors.

	(mimics the signature of :py:class:`subprocess.CalledProcessError`)

	:attribute cmd: Parameters sent to *exiftool* which raised the error
	:attribute returncode: Exit Status (Return code) of the ``execute()`` command which raised the error
	:attribute stdout: STDOUT stream returned by the command which raised the error
	:attribute stderr: STDERR stream returned by the command which raised the error
	"""
	def __init__(self, message, exit_status, cmd_stdout, cmd_stderr, params):
		super().__init__(message)

		self.returncode: int = exit_status
		self.cmd: list = params
		self.stdout: str = cmd_stdout
		self.stderr: str = cmd_stderr


class ExifToolExecuteError(ExifToolExecuteException):
	"""
	ExifTool executed the command but returned a non-zero exit status.

	.. note::
		There is a similarly named :py:exc:`ExifToolExecuteException` which this Error inherits from.

		That is a base class and never returned directly.  This is what is raised.
	"""
	def __init__(self, exit_status, cmd_stdout, cmd_stderr, params):
		super().__init__(f"execute returned a non-zero exit status: {exit_status}", exit_status, cmd_stdout, cmd_stderr, params)


########################################################
#################### JSON Exception ####################
########################################################


class ExifToolOutputEmptyError(ExifToolExecuteException):
	"""
	ExifTool execute_json() expected output, but execute() did not return any output on stdout

	This is an error, because if you expect no output, don't use execute_json()

	.. note::
		Only thrown by execute_json()
	"""
	def __init__(self, exit_status, cmd_stdout, cmd_stderr, params):
		super().__init__("execute_json expected output on stdout but got none", exit_status, cmd_stdout, cmd_stderr, params)


class ExifToolJSONInvalidError(ExifToolExecuteException):
	"""
	ExifTool execute_json() expected valid JSON to be returned, but got invalid JSON.

	This is an error, because if you expect non-JSON output, don't use execute_json()

	.. note::
		Only thrown by execute_json()
	"""
	def __init__(self, exit_status, cmd_stdout, cmd_stderr, params):
		super().__init__("execute_json received invalid JSON output from exiftool", exit_status, cmd_stdout, cmd_stderr, params)


#########################################################
#################### Other Exception ####################
#########################################################

class ExifToolVersionError(ExifToolException):
	"""
	Generic Error to represent some version mismatch.
	PyExifTool is coded to work with a range of exiftool versions.  If the advanced params change in functionality and break PyExifTool, this error will be thrown
	"""


class ExifToolTagNameError(ExifToolException):
	"""
	ExifToolHelper found an invalid tag name

	This error is raised when :py:attr:`exiftool.ExifToolHelper.check_tag_names` is enabled, and a bad tag is provided to a method
	"""
	def __init__(self, bad_tag):
		super().__init__(f"Invalid Tag Name found: \"{bad_tag}\"")
