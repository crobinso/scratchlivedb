
import os
import unittest

import scratchlivedb

datadir = os.path.join(os.path.dirname(__file__), "data")
basicdb = os.path.join(datadir, "basic.db")


class Misc(unittest.TestCase):
    """
    Misc collection of DB tests
    """
    maxDiff = None

    def testNoChange(self):
        db = scratchlivedb.ScratchDatabase(basicdb)
        self.assertEquals(db.get_final_content(), file(basicdb).read())
