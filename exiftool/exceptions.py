# -*- coding: utf-8 -*-

"""

This module holds all the custom exceptions thrown by PyExifTool

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
