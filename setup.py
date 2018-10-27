#!/usr/bin/python

from setuptools import setup


setup(
    name='scratchlivedb',
    version="0.0.1",
    description='Library for manipulating Scratch Live DB/crates',
    author='Cole Robinson',
    license="GPLv2+",
    url='https://github.com/crobinso/scratchlivedb',

    packages=['scratchlivedb'],
    entry_points={
        'console_scripts': ['scratchlivedb-tool = scratchlivedb._cli:main'],
    },
)
