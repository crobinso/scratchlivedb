#!/usr/bin/python

import glob
import os
import sys
import unittest

from distutils.core import setup, Command


class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        import coverage

        omit = []
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
            except:
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


class PylintCommand(Command):
    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        files = " scratchlivedb/ tests/ scratchlivedb-tool "
        # Ignore stuff from scriptimports, it's just duplication
        ignorefiles = " scratchlivedbtool.py "

        os.system("pylint " + files + "--ignore " + ignorefiles +
            "--reports=n "
            "--output-format=colorized "
            "--dummy-variables-rgx=\"dummy|ignore*|.*ignore\" "
            # Lines in modules, function size, ...
            "--disable Design "
            # Line length, spacing, ...
            "--disable Format "
            # Duplicate code
            "--disable Similarities "
            # Use of * or **
            "--disable W0142 "
            # Name doesn't match some style regex
            "--disable C0103 "
            # C0111: No docstring
            "--disable C0111 "
            # W0603: Using the global statement
            "--disable W0603 "
            # W0702: Bare exception type
            "--disable W0702 "
            # W0703: Catching too general exception:
            "--disable W0703 "
            # I0012: Warn about pylint messages disabled in comments
            "--disable I0011 "
            # R0201: Method could be a function
            "--disable R0201 "
            # W1401: Anomalous backslash in string
            "--disable W1401 ")

        print "running pep8"
        os.system("pep8 --format=pylint " + files +
            # E125: Continuation indent isn't different from next block
            # E126: continuation line over-indented for hanging indent
            # E128: Not indented for visual style
            # E203: Space before :
            # E203: Space before :
            # E221: Multiple spaces before operator
            # E303: Too many blank lines
            " --ignore E125,E126,E128,E203,E221,E303")


setup(
    name='scratchlivedb',
    version="0.0.1",
    description='Library for manipulating Scratch Live DB/crates',
    author='Cole Robinson',
    license="GPLv2+",
    packages=['scratchlivedb'],

    cmdclass={
        "test" : TestCommand,
        "pylint" : PylintCommand,
    }
)
