
import os

import scratchlivedb

datadir = os.path.join(os.path.dirname(__file__), "data")
testcratefile = os.path.join(datadir, "test.crate")
emptydb = os.path.join(datadir, "empty.db")


def test_crateNoChange():
    """
    Parse and resave the crate, make sure it doesn't change
    """
    db = scratchlivedb.ScratchCrate(testcratefile)
    assert db.get_final_content() == open(testcratefile, "rb").read()
