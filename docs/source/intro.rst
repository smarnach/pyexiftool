************
Introduction
************

.. _introduction:

.. include:: ../../README.rst
	:start-after: DESCRIPTION_START
	:end-before: DESCRIPTION_END

Concepts
========

As noted in the :ref:`introduction <introduction>`, PyExifTool is used to **communicate** with an instance of the external ExifTool process.

.. note::

	PyExifTool cannot do what ExifTool does not do.  If you're not yet familiar with the capabilities of PH's ExifTool, please head over to `ExifTool by Phil Harvey`_ homepage and read up on how to use it, and what it's capable of.

.. _ExifTool by Phil Harvey: https://exiftool.org/

What PyExifTool Is
------------------

* ... is a wrapper for PH's Exiftool, hence it can do everything PH's ExifTool can do.
* ... is a library which adds some helper functionality around ExifTool to make it easier to work with in Python.
* ... is extensible and you can add functionality on top of the base class for your use case.
* ... is supported on any platform which PH's ExifTool runs

What PyExifTool Is NOT
----------------------

* ... is NOT a direct subtitute for Phil Harvey's ExifTool.  The `exiftool` executable must still be installed and available for PyExifTool to use.
* ... is NOT a library which does direct image manipulation (ex. Python Pillow_).

.. _Pillow: https://pillow.readthedocs.io/en/stable/

Nomenclature
============

PyExifTool's namespace is *exiftool*.  Since library name the same name of the tool it's meant to interface with, it can cause some ambiguity when describing it in docs.
Hence, here's some common nomenclature used.

Because the term `exiftool` is overloaded (lowercase, CapWords case, ...) and can mean several things:

* `PH's ExifTool` = Phil Harvey's ExifTool
* ``ExifTool`` in context usually implies ``exiftool.ExifTool``
* `exiftool` when used alone almost always refers to `PH's ExifTool`'s command line executable.  (While Windows is supported with `exiftool.exe` the Linux nomenclature is used throughout the docs)

