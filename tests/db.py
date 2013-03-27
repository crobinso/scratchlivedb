
import os
import unittest

import scratchlivedb

datadir = os.path.join(os.path.dirname(__file__), "data")
basicdb = os.path.join(datadir, "basic.db")
emptydb = os.path.join(datadir, "empty.db")


def get_properties(obj):
    ret = []
    for p in dir(obj.__class__):
        if type(getattr(obj.__class__, p)) == property:
            ret.append(p)
    return ret


class Misc(unittest.TestCase):
    """
    Misc collection of DB tests
    """
    maxDiff = None

    def testNoChange(self):
        """
        Parse and resave the DB, make sure it doesn't change
        """
        db = scratchlivedb.ScratchDatabase(basicdb)
        self.assertTrue(db.get_final_content() == file(basicdb).read())

    def testNoChangeProperties(self):
        """
        Set every property with it's original value, ensure there's no change
        """
        db = scratchlivedb.ScratchDatabase(basicdb)

        for entry in db.entries:
            for propname in get_properties(entry):
                val = getattr(entry, propname)
                if val is None:
                    continue
                setattr(entry, propname, val)

        self.assertTrue(db.get_final_content() == file(basicdb).read())

    def testEmptyDB(self):
        """
        Empty the DB, compare it, make sure it parses correctly
        """
        db = scratchlivedb.ScratchDatabase(basicdb)
        empty = scratchlivedb.ScratchDatabase(emptydb)
        rawempty = file(emptydb).read()

        db.entries = []
        self.assertTrue(db.get_final_content() == rawempty)
        self.assertTrue(empty.get_final_content() == rawempty)
