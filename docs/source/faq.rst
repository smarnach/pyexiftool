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

