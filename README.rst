**********
PyExifTool
**********

.. HIDE_FROM_PYPI_START

.. image:: https://github.com/sylikc/pyexiftool/actions/workflows/lint-and-test.yml/badge.svg
	:alt: GitHub Actions
	:target: https://github.com/sylikc/pyexiftool/actions

.. image:: https://img.shields.io/pypi/v/pyexiftool.svg
	:target: https://pypi.org/project/PyExifTool/


.. HIDE_FROM_PYPI_END


.. DESCRIPTION_START

.. BLURB_START

PyExifTool is a Python library to communicate with an instance of
`Phil Harvey's ExifTool`_ command-line application.

.. _Phil Harvey's ExifTool: https://exiftool.org/


.. BLURB_END

The library provides the class ``exiftool.ExifTool`` that runs the command-line
tool in batch mode and features methods to send commands to that
program, including methods to extract meta-information from one or
more image files.  Since ``exiftool`` is run in batch mode, only a
single instance needs to be launched and can be reused for many
queries.  This is much more efficient than launching a separate
process for every single query.


.. DESCRIPTION_END

.. contents:: Table of Contents
	:depth: 2
	:backlinks: top

Example Usage
=============

Simple example: ::

	import exiftool

	files = ["a.jpg", "b.png", "c.tif"]
	with exiftool.ExifToolHelper() as et:
	    metadata = et.get_metadata(files)
	for d in metadata:
	    print("{:20.20} {:20.20}".format(d["SourceFile"],
	                                     d["EXIF:DateTimeOriginal"]))


.. INSTALLATION_START

Getting PyExifTool
==================

PyPI
------------

Easiest: Install a version from the official `PyExifTool PyPI`_

::

    python -m pip install -U pyexiftool

.. _PyExifTool PyPI: https://pypi.org/project/PyExifTool/


From Source
------------

The source code can be checked out from the github repository with

::

    git clone git://github.com/sylikc/pyexiftool.git

Alternatively, you can download a tarball_.

.. _tarball: https://github.com/sylikc/pyexiftool/tarball/master

Run

::

    python setup.py install [--user|--prefix=<installation-prefix]

to automatically install this module from source.


PyExifTool Dependencies
=======================

Python
------

PyExifTool runs on **Python 3.6+**.  (If you need Python 2.6 support,
please use version v0.4.x).  PyExifTool has been tested on Windows and
Linux, and probably also runs on other Unix-like platforms.

Phil Harvey's exiftool
----------------------

For PyExifTool to function, ``exiftool`` command-line tool must exist on
the system.  If ``exiftool`` is not on the ``PATH``, you can specify the full
pathname to it by using ``ExifTool(executable=<full path>)``.

PyExifTool requires a **minimum version of 12.15** (which was the first
production version of exiftool featuring the options to allow exit status
checks used in conjuction with ``-echo3`` and ``-echo4`` parameters).

To check your ``exiftool`` version:

::

    exiftool -ver


Windows/Mac
^^^^^^^^^^^

Windows/Mac users can download the latest version of exiftool:

::

    https://exiftool.org

Linux
^^^^^

Most current Linux distributions have a package which will install ``exiftool``.
Unfortunately, some do not have the minimum required version, in which case you
will have to `build from source`_.

* Ubuntu
  ::

    sudo apt install libimage-exiftool-perl

* CentOS/RHEL
  ::

    yum install perl-Image-ExifTool

.. _build from source: https://exiftool.org/install.html#Unix


.. INSTALLATION_END


Documentation
=============

The current documentation is available at `sylikc.github.io`_.
It may slightly lag behind the most updated version but will be improved as the
project moves forward.

::

    http://sylikc.github.io/pyexiftool/

.. _sylikc.github.io: http://sylikc.github.io/pyexiftool/


Package Structure
-----------------

.. DESIGN_INFO_START

PyExifTool was designed with flexibility and extensibility in mind.  The library consists of a few classes, each with increasingly more features.

The base ``ExifTool`` class contains the core functionality exposed in the most rudimentary way, and each successive class inherits and adds functionality.

.. DESIGN_INFO_END

.. DESIGN_CLASS_START

* ``exiftool.ExifTool`` is the base class with core logic to interface with PH's ExifTool process.
  It contains only the core features with no extra fluff.
  The main methods provided are ``execute()`` and ``execute_json()`` which allows direct interaction with the underlying exiftool process.

  * The API is considered stable and should not change much with future releases.

* ``exiftool.ExifToolHelper`` exposes some of the most commonly used functionality.  It overloads
  some inherited functions to turn common errors into warnings and adds logic to make
  ``exiftool.ExifTool`` easier to use.
  For example, ``ExifToolHelper`` provides wrapper functions to get metadata, and auto-starts the exiftool instance if it's not running (instead of raising an Exception).
  ``ExifToolHelper`` demonstrates how to extend ``ExifTool`` to your liking if your project demands customizations not directly provided by ``ExifTool``.

  * More methods may be added and/or slight API tweaks may occur with future releases.

* ``exiftool.ExifToolAlpha`` further extends the ``ExifToolHelper`` and includes some community-contributed not-very-well-tested methods.
  These methods were formerly added ad-hoc by various community contributors, but no longer stand up to the rigor of the current design.
  ``ExifToolAlpha`` is *not* up to the rigorous testing standard of both
  ``ExifTool`` or ``ExifToolHelper``.  There may be old, buggy, or defunct code.

  * This is the least polished of the classes and functionality/API may be changed/added/removed on any release.

  * **NOTE: The methods exposed may be changed/removed at any time.**

  * If you are using any of these methods in your project, please `Submit an Issue`_ to start a discussion on making those functions more robust, and making their way into ``ExifToolHelper``.
    (Think of ``ExifToolAlpha`` as ideas on how to extend ``ExifTool``, where new functionality which may one day make it into the ``ExifToolHelper`` class.)

.. _Submit an Issue: https://github.com/sylikc/pyexiftool/issues


.. DESIGN_CLASS_END


Brief History
=============

.. HISTORY_START

PyExifTool was originally developed by `Sven Marnach`_ in 2012 to answer a
stackoverflow question `Call exiftool from a python script?`_.  Over time,
Sven refined the code, added tests, documentation, and a slew of improvements.
While PyExifTool gained popularity, Sven `never intended to maintain it`_ as
an active project.  The `original repository`_ was last updated in 2014.

Over the years, numerous issues were filed and several PRs were opened on the
stagnant repository.  In early 2019, `Martin Čarnogurský`_ created a
`PyPI release`_ from the 2014 code with some minor updates.  Coincidentally in
mid 2019, `Kevin M (sylikc)`_ forked the original repository and started merging
the PR and issues which were reported on Sven's issues/PR page.

In late 2019 and early 2020 there was a discussion started to
`Provide visibility for an active fork`_.  There was a conversation to
transfer ownership of the original repository, have a coordinated plan to
communicate to PyExifTool users, amongst other things, but it never materialized.

Kevin M (sylikc) made the first release to the PyPI repository in early 2021.
At the same time, discussions were started, revolving around
`Deprecating Python 2.x compatibility`_ and `refactoring the code and classes`_.

The latest version is the result of all of those discussions, designs,
and development.  Special thanks to the community contributions, especially
`Jan Philip Göpfert`_, `Seth P`_, and `Kolen Cheung`_.

.. _Sven Marnach: https://github.com/smarnach/pyexiftool
.. _Call exiftool from a python script?: https://stackoverflow.com/questions/10075115/call-exiftool-from-a-python-script/10075210#10075210
.. _never intended to maintain it: https://github.com/smarnach/pyexiftool/pull/31#issuecomment-569238073
.. _original repository: https://github.com/smarnach/pyexiftool
.. _Martin Čarnogurský: https://github.com/RootLUG
.. _PyPI release: https://pypi.org/project/PyExifTool/0.1.1/#history
.. _Kevin M (sylikc): https://github.com/sylikc
.. _Provide visibility for an active fork: https://github.com/smarnach/pyexiftool/pull/31
.. _Deprecating Python 2.x compatibility: https://github.com/sylikc/pyexiftool/discussions/9
.. _refactoring the code and classes: https://github.com/sylikc/pyexiftool/discussions/10
.. _Jan Philip Göpfert: https://github.com/jangop
.. _Seth P: https://github.com/csparker247
.. _Kolen Cheung: https://github.com/ickc


.. HISTORY_END

Licence
=======

.. LICENSE_START

PyExifTool is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the licence, or
(at your option) any later version, or the BSD licence.

PyExifTool is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See ``LICENSE`` for more details.


.. LICENSE_END
