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


.. _`rose.jpg in tests`: https://github.com/sylikc/pyexiftool/blob/master/tests/images/rose.jpg

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

Read the documentation for the ExifTool constructor ``common_args`` parameter for more details: :py:meth:`exiftool.ExifTool.__init__`.

(You can also change ``common_args`` on an existing instance using :py:attr:`exiftool.ExifTool.common_args`, as long as the subprocess is not :py:attr:`exiftool.ExifTool.running`)

Ways to make the ouptut match
-----------------------------

So if you want to have the ouput match (useful for debugging) between PyExifTool and exiftool, either:

* **Enable print conversion on exiftool command line**:

$ ``exiftool -G -n -JFIF:all rose.jpg``

	.. code-block:: text

		[JFIF]          JFIF Version                    : 1 1
		[JFIF]          Resolution Unit                 : 1
		[JFIF]          X Resolution                    : 72
		[JFIF]          Y Resolution                    : 72

* **Disable print conversion and grouping in PyExifTool**:

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
