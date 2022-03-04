# PyExifTool <http://github.com/sylikc/pyexiftool>
# Copyright 2012 Sven Marnach, Kevin M (sylikc)

# This file is part of PyExifTool.
#
# PyExifTool is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the licence, or
# (at your option) any later version, or the BSD licence.
#
# PyExifTool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING.GPL or COPYING.BSD for more details.

# this "could" still be used, but not the industry recommended option -- https://stackoverflow.com/questions/25337706/setuptools-vs-distutils-why-is-distutils-still-a-thing
#from distutils.core import setup

# recommended packager, though must be installed via PyPI
# https://packaging.python.org/tutorials/packaging-projects/#configuring-metadata
from setuptools import setup, find_packages

import re

def get_long_desc():
	""" read README.rst without the badges (don't need those showing up on PyPI) """

	with open("README.rst", "r", encoding="utf-8") as fh:
		long_desc = fh.read()

	# crop out the portion between HIDE_FROM_PYPI_START and HIDE_FROM_PYPI_END
	sub_pattern = r"^\.\. HIDE_FROM_PYPI_START.+\.\. HIDE_FROM_PYPI_END$"
	long_desc = re.sub(sub_pattern, "", long_desc, flags=re.MULTILINE | re.DOTALL)

	return long_desc


setup(
	# detailed list of options:
	# https://packaging.python.org/guides/distributing-packages-using-setuptools/

	# overview
	name="PyExifTool",
	# version is configured in setup.cfg - https://packaging.python.org/en/latest/guides/single-sourcing-package-version/
	#version=,
	license="GPLv3+/BSD",
	url="http://github.com/sylikc/pyexiftool",
	python_requires=">=3.6",

	# authors
	author="Sven Marnach, Kevin M (sylikc), various contributors",
	author_email="sylikc@gmail.com",

	# info
	description="Python wrapper for exiftool",
	long_description=long_desc,
	long_description_content_type="text/x-rst",
	keywords="exiftool image exif metadata photo video photography",

	project_urls={
		"Documentation": "https://sylikc.github.io/pyexiftool/",
		"Tracker": "https://github.com/sylikc/pyexiftool/issues",
		"Source": "https://github.com/sylikc/pyexiftool",
	},


	classifiers=[
		# list is here:
		# https://pypi.org/classifiers/

		"Development Status :: 3 - Alpha",

		"Intended Audience :: Developers",

		"License :: OSI Approved :: BSD License",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",

		"Operating System :: OS Independent",

		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.6",

		"Topic :: Multimedia",
		"Topic :: Utilities",
	],


	packages=find_packages(
		where=".",
		exclude = ['test*','doc*']
	),

	extras_require={
			"json": ["ujson"],  # supported option for ExifTool, but not currently advertised
			"test": ["packaging"],  # dependencies to do tests
			"docs": ["packaging", "sphinx", "sphinx-autoapi", "sphinx-rtd-theme", "sphinx-autodoc-typehints"],  # dependencies to build docs
		},

	#package_dir={'exiftool': 'exiftool'},

	#py_modules=["exiftool"], - it is now the exiftool module
)
