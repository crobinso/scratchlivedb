
import os
import unittest

import scratchlivedb

datadir = os.path.join(os.path.dirname(__file__), "data")
testcratefile = os.path.join(datadir, "test.crate")
emptydb = os.path.join(datadir, "empty.db")


class Misc(unittest.TestCase):
    """
    Misc collection of crate tests
    """
    maxDiff = None

    def testNoChange(self):
        """
        Parse and resave the crate, make sure it doesn't change
        """
        db = scratchlivedb.ScratchCrate(testcratefile)
        self.assertTrue(db.get_final_content() == file(testcratefile).read())
