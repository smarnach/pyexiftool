***************
Release Process
***************

This page documents the steps to be taken to release a new version of PyExifTool.


Source Preparation
==================

#. Update the version number in ``exiftool/__init__.py``
#. Update the docs copyright year ``docs/source/conf.py`` and in source files
#. Add any changelog entries to ``CHANGELOG.md``
#. Run Tests
#. Generate docs
#. Commit and push the changes.
#. Check that the tests passed on GitHub.


Pre-Requisites
==============

Make sure the latest packages are installed.

#. pip: ``python -m pip install --upgrade pip``
#. build tools: ``python -m pip install --upgrade setuptools build``
#. for uploading to PyPI: ``python -m pip install --upgrade twine``

Run Tests
=========

#. Run in standard unittest: ``python -m unittest -v``
#. Run in PyTest: ``scripts\pytest.bat``

Build and Check
===============

#. Build package: ``python -m build``
#. `Validating reStructuredText markup`_: ``python -m twine check dist/*``

.. _Validating reStructuredText markup: https://packaging.python.org/guides/making-a-pypi-friendly-readme/#validating-restructuredtext-markup

Upload to Test PyPI
===================

Set up the ``$HOME/.pypirc`` (Linux) or ``%UserProfile%\.pypirc`` (Windows)

#. ``python -m twine upload --repository testpypi dist/*``
#. Check package uploaded properly: `TestPyPI PyExifTool`_
#. Create a temporary venv to test PyPI and run tests

	#. ``python -m venv tmp``
	#. Activate venv
	#. ``python -m pip install -U -i https://test.pypi.org/simple/ PyExifTool``

		* If there is an error with SSL verification, just trust it: ``python -m pip install --trusted-host test-files.pythonhosted.org -U -i https://test.pypi.org/simple/ PyExifTool``
		* If you want to test a specific version, can specify as ``PyExifTool==<version>``, otherwise it installs the latest by default

	#. Make sure exiftool is found on PATH
	#. Run tests: ``python -m pytext -v <path to tests directory>``

#. Examine files installed to make sure it looks ok

#. Cleanup: ``python -m pip uninstall PyExifTool``, then delete temp venv


.. _`TestPyPI PyExifTool`: https://test.pypi.org/project/PyExifTool/#history

Release
=======

#. Be very sure all the tests pass and the package is good, because `PyPI does not allow for a filename to be reused`_
#. Release to production PyPI: ``python -m twine upload dist/*``
#. If needed, create a tag, and a GitHub release with the *whl* file

	.. code-block:: bash

		git tag -a vX.X.X
		git push --tags

.. _PyPI does not allow for a filename to be reused: https://pypi.org/help/#file-name-reuse

