***************
Release Process
***************

This page documents the steps to be taken to release a new version of PyExifTool.


Source Preparation
==================

1. Update the version number in ``exiftool/__init__.py``
2. Add any changelog entries to ``CHANGELOG.md``
3. Run Tests
4. Generate docs
5. Commit and push the changes.
6. Check that the tests passed on GitHub.


Pre-Requisites
==============

Make sure the latest packages are installed.

1. pip: ``python -m pip install --upgrade pip``
2. build tools: ``python -m pip install --upgrade setuptools build``
3. for uploading to PyPI: ``python -m pip install --upgrade twine``

Run Tests
=========

1. Run in standard unittest: ``python -m unittest -v``
2. Run in PyTest: ``scripts\pytest.bat``

Build and Check
===============

1. Build package: ``python -m build``
2. `Validating reStructuredText markup`_: ``python -m twine check dist/*``

.. _Validating reStructuredText markup: https://packaging.python.org/guides/making-a-pypi-friendly-readme/#validating-restructuredtext-markup

Upload to Test PyPI
===================

Set up the ``$HOME/.pypirc`` (Linux) or ``%UserProfile%\.pypirc`` (Windows)

1. ``python -m twine upload --repository testpypi dist/*``
2. Check package uploaded properly: `TestPyPI PyExifTool`_
3. Test in a new temporary venv: ``python -m pip install -U -i https://test.pypi.org/simple/ PyExifTool==<version>``

   * If there is an error with SSL verification, just trust it: ``python -m pip install --trusted-host test-files.pythonhosted.org -U -i https://test.pypi.org/simple/ PyExifTool==<version>``

4. Run tests and examine files installed

5. Cleanup: ``python -m pip uninstall PyExifTool``, then delete temp venv

.. _TestPyPI PyExifTool: https://test.pypi.org/project/PyExifTool/#history

Release
=======

1. Be very sure all the tests pass and the package is good, because `PyPI does not allow for a filename to be reused`_
2. Release to production PyPI: ``python -m twine upload dist/*``
3. If needed, create a tag, and a GitHub release with the *whl* file

	.. code-block:: bash

		git tag -a vX.X.X
		git push --tags

.. _PyPI does not allow for a filename to be reused: https://pypi.org/help/#file-name-reuse

