
import os
import unittest

import tests

datadir = os.path.join(os.path.dirname(__file__), "data")
basicdb = os.path.join(datadir, "basic.db")


class Cli(unittest.TestCase):
    """
    Tests for running scratchlivedb-tool
    """
    maxDiff = None

    def testBasic(self):
        """
        Smoke test for the CLI tool
        """
        tests.clicomm("scratchlivedb-tool %s" % basicdb)
