**********************
Examples / Quick Start
**********************

.. NOTE: No tabs in this file, all spaces, to simplify examples indentation


Try it yourself: All of these examples are using the images provided in the `tests directory`_ in the source

.. _`tests directory`: https://github.com/sylikc/pyexiftool/tree/master/tests/images



Understanding input and output from PyExifTool base methods
===========================================================

Almost all methods in PyExifTool revolve around the usage of two methods from the base :py:class:`exiftool.ExifTool` class.


**It is important to understand the ouput from each of these commands**, so here's a quick summary (you can click through to the API to read more details)

.. note::

    Because both methods are inherited by :py:class:`exiftool.ExifToolHelper` and :py:class:`exiftool.ExifToolAlpha`, you can call it from those classes as well.


.. _examples input params:

Input parameters
----------------

Both methods take an argument list ``*args``.  Examples:

.. note::

    As a general rule of thumb, if there is an **unquoted space on the command line** to *exiftool*, it's a **separate argument to the method** in PyExifTool.

    If you have a working `exiftool` command-line but having trouble figuring out how to properly separate the arguments, please refer to the :ref:`FAQ <shlex split>`

* Calling directly:

    * exiftool command-line:

        .. code-block:: text

            exiftool -XMPToolKit -Subject rose.jpg

    * PyExifTool:

        .. code-block::

            execute("-XMPToolKit", "-Subject", "rose.jpg")

* Using argument unpacking of a list:

    * exiftool command-line:

        .. code-block:: text

            exiftool -P -DateTimeOriginal="2021:01:02 03:04:05" -MakerNotes= "spaces in filename.jpg"

    * PyExifTool:

        .. note::

            Parameters which need to be quoted on the command line generally do not need to be quoted in the parameters to PyExifTool.  In fact, quoting may have unintended behavior.

            In this example, *DateTimeOriginal* value is not quoted in the parameter to execute().

        .. code-block::

            execute(*["-P", "-DateTimeOriginal=2021:01:02 03:04:05", "-MakerNotes=", "spaces in filename.jpg"])


* Getting JSON output using argument unpacking of a list:

    * exiftool command-line:

        .. code-block:: text

            exiftool -j -XMP:all -JFIF:JFIFVersion /path/somefile.jpg

    * PyExifTool:

        .. code-block::

            execute_json(*["-XMP:all", "-JFIF:JFIFVersion", "/path/somefile.jpg"])


Output values
-------------

* :py:meth:`exiftool.ExifTool.execute_json`

    * Returns a ``list`` of ``dict``
    * Each ``dict`` is a result from a file
    * Each ``dict`` contains a key "SourceFile" which points to the relative or absolute file path of file
    * All other keys/value pairs are requested metadata

* :py:meth:`exiftool.ExifTool.execute`

    * Returns a ``str``
    * Typically used for **setting tags** as no values are returned in that case.


ExifToolHelper
==============

Using methods provided by :py:class:`exiftool.ExifToolHelper`:

ExifToolHelper provides some of the most commonly used operations most people use *exiftool* for

Getting Tags
------------

* Get all tags on a single file

    .. code-block::

        from exiftool import ExifToolHelper
        with ExifToolHelper() as et:
            for d in et.get_metadata("rose.jpg"):
                for k, v in d.items():
                    print(f"Dict: {k} = {v}")


    .. code-block:: text

        Dict: SourceFile = rose.jpg
        Dict: ExifTool:ExifToolVersion = 12.37
        Dict: File:FileName = rose.jpg
        Dict: File:Directory = .
        Dict: File:FileSize = 4949
        Dict: File:FileModifyDate = 2022:03:03 17:47:11-08:00
        Dict: File:FileAccessDate = 2022:03:27 08:28:16-07:00
        Dict: File:FileCreateDate = 2022:03:03 17:47:11-08:00
        Dict: File:FilePermissions = 100666
        Dict: File:FileType = JPEG
        Dict: File:FileTypeExtension = JPG
        Dict: File:MIMEType = image/jpeg
        Dict: File:ImageWidth = 70
        Dict: File:ImageHeight = 46
        Dict: File:EncodingProcess = 0
        Dict: File:BitsPerSample = 8
        Dict: File:ColorComponents = 3
        Dict: File:YCbCrSubSampling = 2 2
        Dict: JFIF:JFIFVersion = 1 1
        Dict: JFIF:ResolutionUnit = 1
        Dict: JFIF:XResolution = 72
        Dict: JFIF:YResolution = 72
        Dict: XMP:XMPToolkit = Image::ExifTool 8.85
        Dict: XMP:Subject = Röschen
        Dict: Composite:ImageSize = 70 46
        Dict: Composite:Megapixels = 0.00322

* Get some tags in multiple files

    .. code-block::

        from exiftool import ExifToolHelper
        with ExifToolHelper() as et:
            for d in et.get_tags(["rose.jpg", "skyblue.png"], tags=["FileSize", "ImageSize"]):
                for k, v in d.items():
                    print(f"Dict: {k} = {v}")


    .. code-block:: text

        Dict: SourceFile = rose.jpg
        Dict: File:FileSize = 4949
        Dict: Composite:ImageSize = 70 46
        Dict: SourceFile = skyblue.png
        Dict: File:FileSize = 206
        Dict: Composite:ImageSize = 64 64

Setting Tags
------------

* Setting date and time of some files to current time, overwriting file, but preserving original mod date

    .. code-block::

        from exiftool import ExifToolHelper
        from datetime import datetime
        with ExifToolHelper() as et:
            now = datetime.strftime(datetime.now(), "%Y:%m:%d %H:%M:%S")
            et.set_tags(
                ["rose.jpg", "skyblue.png"],
                tags={"DateTimeOriginal": now},
                params=["-P", "-overwrite_original"]
            )

    (*No output is returned if successful*)

* Setting keywords for a file.

    .. code-block::

        from exiftool import ExifToolHelper
        with ExifToolHelper() as et:
            et.set_tags(
                ["rose.jpg", "skyblue.png"],
                tags={"Keywords": ["sunny", "nice day", "cool", "awesome"]}
            )

    (*No output is returned if successful*)



Exceptions
----------

By default, ExifToolHelper has some **built-in error checking**, making the methods safer to use than calling the base methods directly.

.. warning::

    While "safer", the error checking isn't fool-proof.  There are a lot of cases where *exiftool* just silently ignores bad input and doesn't indicate an error.

* Example using get_tags() on a list which includes a non-existent file

    * ExifToolHelper with error-checking, using :py:meth:`exiftool.ExifToolHelper.get_tags`

        .. code-block::

            from exiftool import ExifToolHelper
            with ExifToolHelper() as et:
                print(et.get_tags(
                    ["rose.jpg", "skyblue.png", "non-existent file.tif"],
                    tags=["FileSize"]
                ))

        Output:

        .. code-block:: text

            Traceback (most recent call last):
              File "T:\example.py", line 7, in <module>
                et.get_tags(["rose.jpg", "skyblue.png", "non-existent file.tif"], tags=["FileSize"])
              File "T:\pyexiftool\exiftool\helper.py", line 353, in get_tags
                ret = self.execute_json(*exec_params)
              File "T:\pyexiftool\exiftool\exiftool.py", line 1030, in execute_json
                result = self.execute("-j", *params)  # stdout
              File "T:\pyexiftool\exiftool\helper.py", line 119, in execute
                raise ExifToolExecuteError(self._last_status, self._last_stdout, self._last_stderr, params)
            exiftool.exceptions.ExifToolExecuteError: execute returned a non-zero exit status: 1


    * ExifTool only, without error checking, using :py:meth:`exiftool.ExifTool.execute_json` (**Note how the missing file is silently ignored and doesn't show up in returned list.**)

        .. code-block::

            from exiftool import ExifToolHelper
            with ExifToolHelper() as et:
                print(et.get_tags(
                    ["rose.jpg", "skyblue.png", "non-existent file.tif"],
                    tags=["FileSize"]
                ))

        Output:

        .. code-block:: text

            [{'SourceFile': 'rose.jpg', 'File:FileSize': 4949}, {'SourceFile': 'skyblue.png', 'File:FileSize': 206}]


* Example using :py:meth:`exiftool.ExifToolHelper.get_tags` with a typo.  Let's say you wanted to ``get_tags()``, but accidentally copy/pasted something and left a ``=`` character behind (deletes tag rather than getting!)...

    * Using :py:meth:`exiftool.ExifToolHelper.get_tags`

        .. code-block::

            from exiftool import ExifToolHelper
            with ExifToolHelper() as et:
                print(et.get_tags(["skyblue.png"], tags=["XMP:Subject=hi"]))

        Output:

        .. code-block:: text

            Traceback (most recent call last):
              File "T:\example.py", line 7, in <module>
                print(et.get_tags(["skyblue.png"], tags=["XMP:Subject=hi"]))
              File "T:\pyexiftool\exiftool\helper.py", line 341, in get_tags
                self.__class__._check_tag_list(final_tags)
              File "T:\pyexiftool\exiftool\helper.py", line 574, in _check_tag_list
                raise ExifToolTagNameError(t)
            exiftool.exceptions.ExifToolTagNameError: Invalid Tag Name found: "XMP:Subject=hi"

    * Using :py:meth:`exiftool.ExifTool.execute_json`.  It still raises an exception, but more cryptic and difficult to debug

        .. code-block::

            from exiftool import ExifTool
            with ExifTool() as et:
                print(et.execute_json(*["-XMP:Subject=hi"] + ["skyblue.png"]))

        Output:

        .. code-block:: text

            Traceback (most recent call last):
              File "T:\example.py", line 7, in <module>
                print(et.execute_json(*["-XMP:Subject=hi"] + ["skyblue.png"]))
              File "T:\pyexiftool\exiftool\exiftool.py", line 1052, in execute_json
                raise ExifToolOutputEmptyError(self._last_status, self._last_stdout, self._last_stderr, params)
            exiftool.exceptions.ExifToolOutputEmptyError: execute_json expected output on stdout but got none

    * Using :py:meth:`exiftool.ExifTool.execute`.  **No errors, but you have now written to the file instead of reading from it!**

        .. code-block::

            from exiftool import ExifTool
            with ExifTool() as et:
                print(et.execute(*["-XMP:Subject=hi"] + ["skyblue.png"]))

        Output:

        .. code-block:: text

            1 image files updated

ExifTool
========

Using methods provided by :py:class:`exiftool.ExifTool`

Calling execute() or execute_json() provides raw functionality for advanced use cases.  Use with care!



.. TODO show some ExifTool and ExifToolHelper use cases for common exiftool operations

.. TODO show some Advanced use cases, and maybe even some don't-do-this-even-though-you-can cases (like using params for tags)

