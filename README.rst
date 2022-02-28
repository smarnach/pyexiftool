**********
PyExifTool
**********

PyExifTool is a Python library to communicate with an instance of Phil
Harvey's excellent ExifTool_ command-line application.  The library
provides the class ``exiftool.ExifTool`` that runs the command-line
tool in batch mode and features methods to send commands to that
program, including methods to extract meta-information from one or
more image files.  Since ``exiftool`` is run in batch mode, only a
single instance needs to be launched and can be reused for many
queries.  This is much more efficient than launching a separate
process for every single query.

.. _ExifTool: https://exiftool.org/

Example Usage
=============

.. code-block:: python
	:caption: Quick Sample
	:linenos:

	import exiftool

	files = ["a.jpg", "b.png", "c.tif"]
	with exiftool.ExifToolHelper() as et:
		metadata = et.get_metadata(files)
	for d in metadata:
		print("{:20.20} {:20.20}".format(d["SourceFile"],
										 d["EXIF:DateTimeOriginal"]))


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


Documentation
=============

The documentation is available at `sylikc.github.io`_.
It is slightly outdated at the moment but will be improved as the
project moves forward

::

    http://sylikc.github.io/pyexiftool/

.. _sylikc.github.io: http://sylikc.github.io/pyexiftool/


Package Structure
-----------------

PyExifTool consists of a few modules, each with increasingly more features.

The base ``ExifTool`` class is the most rudimentary, and each successive class
inherits and adds functionality.

* ``ExifTool`` is the base class with functionality which will not likely change.
  It contains the core features with no extra fluff.  The API is considered stable
  and should not change much with new versions.

* ``ExifToolHelper`` adds the most commonly used functionality.  It overloads
  some functions to turn common errors into warnings or makes checks to make
  ``ExifTool`` easier to use.  More methods may be added or slight tweaks may
  come with new versions.

* ``ExifToolAlpha`` includes some of the community functionality that contributors
  added for edge use cases.  It is *not* up to the rigorous testing standard of both
  ``ExifTool`` or ``ExifToolHelper``.  There may be old or defunct code at any time.
  This is the least polished of the classes and functionality/API may be
  changed/added/removed at any time.


Brief History
=============

PyExifTool was originally developed by `Sven Marnach`_ in 2012 to answer a
stackoverflow question `Call exiftool from a python script?`_.  Over time,
Sven refined the code, added tests, documentation, and a slew of improvements.
While PyExifTool gained popularity, Sven `never intended to maintain it`_ as
an active project.  The `original repository`_ was last updated in 2014.

In early 2019, `Martin Čarnogurský`_ created a `PyPI release`_ from the
2014 code.  Coincidentally in mid 2019, `Kevin M (sylikc)`_ forked the original
repository and started merging PR and issues which were reported on Sven's
issues/PR page.

In late 2019 and early 2020 there was a discussion started to
`Provide visibility for an active fork`_.  There was a conversation to
transfer ownership of the original repository, have a coordinated plan to
communicate to PyExifTool users, amongst other things, but it never materialized.

Kevin M (sylikc) made the first release to PyPI repository in early 2021.
At the same time, discussions were starting revolving around
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

Licence
=======

PyExifTool is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the licence, or
(at your option) any later version, or the BSD licence.

PyExifTool is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See ``LICENSE`` for more details.
