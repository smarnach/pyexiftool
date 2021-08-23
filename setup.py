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

with open("README.rst", "r", encoding="utf-8") as fh:
	long_desc = fh.read()

setup(
	# detailed list of options:
	# https://packaging.python.org/guides/distributing-packages-using-setuptools/
	
	# overview
	name="PyExifTool",
	version="0.4.11",
	license="GPLv3+/BSD",
	url="http://github.com/sylikc/pyexiftool",
	python_requires=">=2.6",
	
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
		
		"Programming Language :: Python :: 2.6",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3",
		
		"Topic :: Multimedia",
		"Topic :: Utilities",
	],
	
	
	packages=find_packages(
		where=".",
		exclude = ['test*',]
	),
	
	#py_modules=["exiftool"], - it is now the exiftool module
)
