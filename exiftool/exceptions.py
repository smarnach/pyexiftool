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

This submodule holds all of the custom exceptions which can be raised by PyExifTool

"""

class ExifToolException(Exception):
	"""
	Generic Base class for all ExifTool error classes
	"""


class ExifToolVersionError(ExifToolException):
	"""
	Generic Error to represent some version mismatch.
	PyExifTool is coded to work with a range of exiftool versions.  If the advanced params change in functionality and break PyExifTool, this error will be thrown
	"""


class ProcessStateError(ExifToolException):
	"""
	Base class for all errors related to the invalid state of `exiftool` subprocess
	"""

class ExifToolRunning(ProcessStateError):
	"""
	ExifTool is already running
	"""
	def __init__(self, message):
		super().__init__(f"ExifTool instance is running: {message}")

class ExifToolNotRunning(ProcessStateError):
	"""
	ExifTool is not running
	"""
	def __init__(self, message):
		super().__init__(f"ExifTool instance not running: {message}")



class OutputEmpty(ExifToolException):
	"""
	ExifTool did not return output, only thrown by execute_json()
	"""

class OutputNotJSON(ExifToolException):
	"""
	ExifTool did not return valid JSON, only thrown by execute_json()
	"""


class ExifToolExecuteError(ExifToolException):
	"""
	ExifTool executed the command but returned a non-zero exit status

	(mimics the signature of :py:class:`subprocess.CalledProcessError`)

	:attribute returncode: Exit Status (Return code) of the ``execute()`` command which raised the error
	:attribute cmd: Parameters sent to *exiftool* which raised the error
	:attribute stdout: STDOUT stream returned by the command which raised the error
	:attribute stderr: STDERR stream returned by the command which raised the error
	"""
	def __init__(self, exit_status, cmd_stdout, cmd_stderr, params):
		super().__init__(f"Exiftool execute returned a non-zero exit status: {exit_status}")

		self.returncode: int = exit_status
		self.cmd: list = params
		self.stdout: str = cmd_stdout
		self.stderr: str = cmd_stderr

