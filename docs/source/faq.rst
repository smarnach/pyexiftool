**************************
Frequently Asked Questions
**************************

PyExifTool output is different from the exiftool command line
=============================================================

One of the most frequently asked questions relates to the *default output* of PyExifTool.

For example, using the `rose.jpg in tests`_, let's get **all JFIF tags**:

Default exiftool output
-----------------------

$ ``exiftool -JFIF:all rose.jpg``

.. code-block:: text

	JFIF Version                    : 1.01
	Resolution Unit                 : inches
	X Resolution                    : 72
	Y Resolution                    : 72


.. _`rose.jpg in tests`: https://github.com/sylikc/pyexiftool/blob/master/tests/files/rose.jpg

Default PyExifTool output
-------------------------

from PyExifTool, using the following code:

.. code-block::

	import exiftool
	with exiftool.ExifTool() as et:
	    print(et.execute("-JFIF:all", "rose.jpg"))

Output:

.. code-block:: text

	[JFIF]          JFIF Version                    : 1 1
	[JFIF]          Resolution Unit                 : 1
	[JFIF]          X Resolution                    : 72
	[JFIF]          Y Resolution                    : 72

What's going on?
----------------

The reason for the different default output is that PyExifTool, by default, includes two arguments which make *exiftool* easier to use: ``-G, -n``.

.. note::

	The ``-n`` disables *print conversion* which displays **raw tag values**, making the output more **machine-parseable**.

	When *print conversion* is enabled, *some* raw values may be translated to prettier **human-readable** text.


.. note::
	The ``-G`` enables *group name (level 1)* option which displays a group in the output to help disambiguate tags with the same name in different groups.

	For example, *-DateCreated* can be ambiguous if both *-IPTC:DateCreated* and *-XMP:DateCreated* exists and have different values.  ``-G`` would display which one was returned by *exiftool*.


Read the documentation for the ExifTool constructor ``common_args`` parameter for more details: :py:meth:`exiftool.ExifTool.__init__`.

(You can also change ``common_args`` on an existing instance using :py:attr:`exiftool.ExifTool.common_args`, as long as the subprocess is not :py:attr:`exiftool.ExifTool.running`)




Ways to make the ouptut match
-----------------------------

So if you want to have the ouput match (*useful for debugging*) between PyExifTool and exiftool, either:

* **Enable print conversion on exiftool command line**:

	$ ``exiftool -G -n -JFIF:all rose.jpg``

	.. code-block:: text

		[JFIF]          JFIF Version                    : 1 1
		[JFIF]          Resolution Unit                 : 1
		[JFIF]          X Resolution                    : 72
		[JFIF]          Y Resolution                    : 72

* **Disable print conversion and group name in PyExifTool**:

	.. code-block::

		import exiftool
		with exiftool.ExifTool(common_args=None) as et:
		    print(et.execute("-JFIF:all", "rose.jpg"))

	Output:

	.. code-block:: text

		JFIF Version                    : 1.01
		Resolution Unit                 : inches
		X Resolution                    : 72
		Y Resolution                    : 72



.. _shlex split:

I can run this on the command-line but it doesn't work in PyExifTool
====================================================================

A frequent problem encountered by first-time users, is figuring out how to properly split their arguments into a call to PyExifTool.

As noted in the :ref:`Quick Start Examples <examples input params>`:

	If there is an **unquoted space on the command line** to *exiftool*, it's a **separate argument to the method** in PyExifTool.

So, what does this look like in practice?

Use `Python's shlex library`_ as a quick and easy way to figure out what the parameters to :py:meth:`exiftool.ExifTool.execute` or :py:meth:`exiftool.ExifTool.execute_json` should be.

* Sample exiftool command line (with multiple quoted and unquoted parameters):

	.. code-block:: text

		exiftool -v0 -preserve -overwrite_original -api largefilesupport=1 -api "QuickTimeUTC=1" "-EXIF:DateTimeOriginal+=1:2:3 4:5:6" -XMP:DateTimeOriginal="2006:05:04 03:02:01" -gpsaltituderef="Above Sea Level" -make= test.mov

* Using ``shlex`` to figure out the right argument list:

	.. code-block::

		import shlex, exiftool
		with exiftool.ExifToolHelper() as et:
			params = shlex.split('-v0 -preserve -overwrite_original -api largefilesupport=1 "-EXIF:DateTimeOriginal+=1:2:3 4:5:6" -XMP:DateTimeOriginal="2006:05:04 03:02:01" -gpsaltituderef="Above Sea Level" -make= test.mov')
			print(params)
			# Output: ['-v0', '-preserve', '-overwrite_original', '-api', 'largefilesupport=1', '-api', 'QuickTimeUTC=1', '-EXIF:DateTimeOriginal+=1:2:3 4:5:6', '-XMP:DateTimeOriginal=2006:05:04 03:02:01', '-gpsaltituderef=Above Sea Level', '-make=', 'test.mov']
			et.execute(*params)

	.. note::

		``shlex.split()`` is a useful *tool to simplify discovery* of the correct arguments needed to call PyExifTool.

		However, since spliting and constructing immutable strings in Python is **slower than building the parameter list properly**, this method is *only recommended for* **debugging**!


.. _`Python's shlex library`: https://docs.python.org/library/shlex.html

.. _set_json_loads faq:

PyExifTool json turns some text fields into numbers
===================================================

A strange behavior of *exiftool* is documented in the `exiftool documentation`_::

	-j[[+]=JSONFILE] (-json)

		Note that ExifTool quotes JSON values only if they don't look like numbers
		(regardless of the original storage format or the relevant metadata specification).

.. _`exiftool documentation`: https://exiftool.org/exiftool_pod.html#OPTIONS

This causes a peculiar behavior if you set a text metadata field to a string that looks like a number:

.. code-block::

	import exiftool
	with exiftool.ExifToolHelper() as et:
		# Comment is a STRING field
		et.set_tags("rose.jpg", {"Comment": "1.10"})  # string: "1.10" != "1.1"

		# FocalLength is a FLOAT field
		et.set_tags("rose.jpg", {"FocalLength": 1.10})  # float: 1.10 == 1.1
		print(et.get_tags("rose.jpg", ["Comment", "FocalLength"]))

		# Prints: [{'SourceFile': 'rose.jpg', 'File:Comment': 1.1, 'EXIF:FocalLength': 1.1}]

Workaround to enable output as string
-------------------------------------

There is no universal fix which wouldn't affect other behaviors in PyExifTool, so this is an advanced workaround if you encounter this specific problem.

PyExifTool does not do any processing on the fields returned by *exiftool*.  In effect, what is returned is processed directly by ``json.loads()`` by default.

You can change the behavior of the json string parser, or specify a different one using :py:meth:`exiftool.ExifTool.set_json_loads`.

The `documentation of CPython's json.load`_ allows ``parse_float`` to be any parser of choice when a float is encountered in a JSON file.  Thus, you can force the float to be interpreted as a string.
However, as you can see below, it also *changes the behavior of all float fields*.


.. _`documentation of CPython's json.load`: https://docs.python.org/3/library/json.html#json.load

.. code-block::

	import exiftool, json
	with exiftool.ExifToolHelper() as et:
		et.set_json_loads(json.loads, parse_float=str)

		# Comment is a STRING field
		et.set_tags("rose.jpg", {"Comment": "1.10"})  # string: "1.10" == "1.10"

		# FocalLength is a FLOAT field
		et.set_tags("rose.jpg", {"FocalLength": 1.10})  # float: 1.1 != "1.1"
		print(et.get_tags("rose.jpg", ["Comment", "FocalLength"]))

		# Prints: [{'SourceFile': 'rose.jpg', 'File:Comment': '1.10', 'EXIF:FocalLength': '1.1'}]

.. warning::

	Unfortunately you can either change all float fields to a string, or possibly lose some float precision when working with floats in string metadata fields.

	There isn't any known universal workaround which wouldn't break one thing or the other, as it is an underlying *exiftool* quirk.

There are other edge cases which may exhibit quirky behavior when storing numbers and whitespace only to text fields (See `test cases related to numeric tags`_).  Since PyExifTool cannot accommodate all possible edge cases,
this workaround will allow you to configure PyExifTool to work in your environment!

.. _`test cases related to numeric tags`: https://github.com/sylikc/pyexiftool/blob/master/tests/test_helper_tags_float.py


I would like to use a faster json string parser
===============================================

By default, PyExifTool uses the built-in ``json`` library to load the json string returned by *exiftool*.  If you would like to use an alternate library, set it manually using :py:meth:`exiftool.ExifTool.set_json_loads`


.. code-block::

	import exiftool, json
	with exiftool.ExifToolHelper() as et:
		et.set_json_loads(ujson.loads)
		...

.. note::

	In PyExifTool version before 0.5.6, ``ujson`` was supported automatically if the package was installed.

	To support any possible alternative JSON library, this behavior has now been changed and it must be enabled manually.


I'm getting an error! How do I debug PyExifTool output?
=======================================================

To assist debugging, ExifTool has a ``logger`` in the constructor :py:meth:`exiftool.ExifTool.__init__`.  You can also specify the logger after constructing the object by using the :py:attr:`exiftool.ExifTool.logger` property.

First construct the logger object.  The example below using the most common way to construct using ``getLogger(__name__)``.  See more examples on `Python logging - Advanced Logging Tutorial`_


.. _`Python logging - Advanced Logging Tutorial`: https://docs.python.org/3/howto/logging.html#advanced-logging-tutorial

Example usage:

.. code-block::

	import logging
	import exiftool

	logging.basicConfig(level=logging.DEBUG)
	with exiftool.ExifToolHelper(logger=logging.getLogger(__name__)) as et:
		et.execute("missingfile.jpg",)

