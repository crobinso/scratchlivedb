
import os
import unittest

import tests

datadir = os.path.join(os.path.dirname(__file__), "data")
basicdb = os.path.join(datadir, "basic.db")
unknowndb = os.path.join(datadir, "unknown_keys.db")
rhythmbox_xml = os.path.join(datadir, "rhythmdb.xml")
rhythmbox_scratch_input = os.path.join(datadir, "rhythmbox_sync.db")


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
        out = tests.clicomm("scratchlivedb-tool %s" % unknowndb)
        self.assertTrue(
                "Unknown keys encountered: ['tzzz', 'uzzz', 'zzzz']" in out)

        out = tests.clicomm("scratchlivedb-tool --debug %s" % unknowndb)
        self.assertTrue("Unknown type for key 'zzzz'" in out)


    def testSyncRhythmbox(self):
        """
        Basic test for rhythmbox sync, make sure we see expected output
        """
        out = tests.clicomm("scratchlivedb-tool --dry-run "
                            "--sync-rhythmbox --rhythmdb %s %s" %
                            (rhythmbox_xml, rhythmbox_scratch_input))

        self.assertTrue("Changing timeadded:  Armored_Core/Armored_" in out)
        self.assertTrue("Removing from DB:    Orb/Orb_-_Adv")
