
import atexit
import glob
import os
import unittest

import tests

datadir = os.path.join(os.path.dirname(__file__), "data")
basicdb = os.path.join(datadir, "basic.db")
unknowndb = os.path.join(datadir, "unknown_keys.db")
rmfiles = []


def _cleanup():
    for base in rmfiles:
        for f in glob.glob(base + "*"):
            try:
                os.unlink(f)
            except Exception:
                continue


atexit.register(_cleanup)


class Cli(unittest.TestCase):
    """
    Tests for running scratchlivedb-tool
    """
    maxDiff = None

    def testBasic(self):
        """
        Smoke test for the CLI tool
        """
        tests.clicomm("scratchlivedb-tool dump %s" % basicdb)

    def testUnknownKeys(self):
        """
        Make sure unknown key detection works
        """
        # Prevent unfinished crate support from interfering
        # pylint: disable=protected-access
        # Ignore 'Access to protected member'
        from scratchlivedb.scratchdb import _unknowns
        _unknowns.unknowns = {}
        # pylint: enable=protected-access

        out = tests.clicomm("scratchlivedb-tool dump %s" % unknowndb)
        assert "Unknown keys encountered: ['tzzz', 'uzzz', 'zzzz']" in out

        out = tests.clicomm("scratchlivedb-tool --debug dump %s" % unknowndb)
        assert "Unknown type for key 'zzzz'" in out
