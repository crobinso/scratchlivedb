#!/usr/bin/python

import glob
import os
import sys
import unittest

from distutils.core import Command
from setuptools import setup


class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        import coverage

        cov = coverage.coverage(omit=["/*/tests/*"])
        cov.erase()
        cov.start()

        testfiles = []
        for t in glob.glob(os.path.join(os.getcwd(), 'tests', '*.py')):
            if t.endswith("__init__.py"):
                continue

            base = os.path.basename(t)
            testfiles.append('.'.join(['tests', os.path.splitext(base)[0]]))

        if hasattr(unittest, "installHandler"):
            try:
                unittest.installHandler()
            except Exception:
                print "installHandler hack failed"

        tests = unittest.TestLoader().loadTestsFromNames(testfiles)
        t = unittest.TextTestRunner(verbosity=1)
        result = t.run(tests)

        cov.stop()
        cov.save()

        err = int(bool(len(result.failures) > 0 or
                       len(result.errors) > 0))
        if not err:
            cov.report(show_missing=False)
        sys.exit(err)


setup(
    name='scratchlivedb',
    version="0.0.1",
    description='Library for manipulating Scratch Live DB/crates',
    author='Cole Robinson',
    license="GPLv2+",
    url='https://github.com/crobinso/scratchlivedb',

    packages=['scratchlivedb'],
    entry_points={
        'console_scripts': ['scratchlivedb-tool = scratchlivedb._cli:main']},

    cmdclass={
        "test" : TestCommand,
    }
)
