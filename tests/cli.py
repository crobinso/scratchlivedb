
import atexit
import glob
import os
import shutil
import unittest

import tests

datadir = os.path.join(os.path.dirname(__file__), "data")
basicdb = os.path.join(datadir, "basic.db")
unknowndb = os.path.join(datadir, "unknown_keys.db")
rhythmbox_xml = os.path.join(datadir, "rhythmdb.xml")
rhythmbox_scratch_input = os.path.join(datadir, "rhythmbox_sync.db")
rmfiles = []


def _cleanup():
    for base in rmfiles:
        for f in glob.glob(base + "*"):
            try:
                os.unlink(f)
            except:
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
        tests.clicomm("scratchlivedb-tool %s" % basicdb)

    def testUnknownKeys(self):
        """
        Make sure unknown key detection works
        """
        # Prevent unfinished crate support from interfering
        # pylint: disable=W0212
        # Ignore 'Access to protected member'
        from scratchlivedb.scratchdb import _unknowns
        _unknowns.unknowns = {}
        # pylint: enable=W0212

        out = tests.clicomm("scratchlivedb-tool %s" % unknowndb)
        self.assertTrue(
                "Unknown keys encountered: ['tzzz', 'uzzz', 'zzzz']" in out)

        out = tests.clicomm("scratchlivedb-tool --debug %s" % unknowndb)
        self.assertTrue("Unknown type for key 'zzzz'" in out)


    def testSyncRhythmbox(self):
        """
        Basic test for rhythmbox sync, make sure we see expected output
        """
        tmpfile = rhythmbox_scratch_input + ".tmp"
        shutil.copy(rhythmbox_scratch_input, tmpfile)
        rmfiles.append(tmpfile)

        cmd = ("scratchlivedb-tool --in-place "
               "--sync-rhythmbox --rhythmdb %s %s" %
               (rhythmbox_xml, tmpfile))
        out = tests.clicomm(cmd)

        self.assertTrue("Changing timeadded:  Armored_Core/Armored_" in out)
        self.assertTrue("Removing from DB:    Orb/Orb_-_Adv")
        self.assertTrue("Adding to DB:        Orbital/Orbital_-_In_S" in out)
        self.assertTrue("Adding to DB:        Daft_Punk/Daft_Punk_-_Tr" in out)
        self.assertTrue("Adding to DB:        Advantage/Advantage_-_Th" in out)

        # Make sure running twice doesn't make any changes
        out = tests.clicomm(cmd)
        self.assertTrue("Parsing rhythmbox DB\nBacking up to" in out)
