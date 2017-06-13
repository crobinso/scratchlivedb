# -*- encoding: utf-8 -*-

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

    def testDBDocString(self):
        """
        This is a weird one, but it's for my own sanity. Make sure
        the DB doc string and DB properties are in sync.
        """
        db = scratchlivedb.ScratchDatabase(basicdb)
        doc = db.entries[0].__doc__

        # pylint: disable=W0212
        # Ignore 'Access to protected member'
        rawkeys = scratchlivedb.scratchdb._seen[:]
        # pylint: enable=W0212

        dockeys = []
        for line in doc.splitlines():
            line = line.strip("\n").strip()
            if line[4:6] != " :":
                continue
            dockeys.append(line.split(" :")[0])

        dockeys.sort()
        rawkeys.sort()
        self.assertEqual(dockeys, rawkeys)

    def testNonAscii(self):
        """
        Test formatting non-ASCII filenames
        """
        empty = scratchlivedb.ScratchDatabase(emptydb)
        name = """Users/powermac/Music/Jîcksons -#- Bléme It ün the Boogie (12" Single Version) kopie.mp3"""
        rawname = """\x00U\x00s\x00e\x00r\x00s\x00/\x00p\x00o\x00w\x00e\x00r\x00m\x00a\x00c\x00/\x00M\x00u\x00s\x00i\x00c\x00/\x00J\x00\xee\x00c\x00k\x00s\x00o\x00n\x00s\x00 \x00-\x00#\x00-\x00 \x00B\x00l\x00\xe9\x00m\x00e\x00 \x00I\x00t\x00 \x00\xfc\x00n\x00 \x00t\x00h\x00e\x00 \x00B\x00o\x00o\x00g\x00i\x00e\x00 \x00(\x001\x002\x00"\x00 \x00S\x00i\x00n\x00g\x00l\x00e\x00 \x00V\x00e\x00r\x00s\x00i\x00o\x00n\x00)\x00 \x00k\x00o\x00p\x00i\x00e\x00.\x00m\x00p\x003"""

        entry = empty.make_entry(name)
        self.assertEquals(entry.filebase, name)
        self.assertEquals(entry._rawdict["pfil"], rawname)

    def testAddToDB(self):
        """
        Test adding entries to a DB
        """
        basic = scratchlivedb.ScratchDatabase(basicdb)
        empty = scratchlivedb.ScratchDatabase(emptydb)

        empty.entries.append(basic.entries[10])
        empty.entries.append(basic.entries[20])

        newentry = empty.make_entry("foo/some/file/path")
        newentry.tracktitle = "Hey a track title"
        empty.entries.append(newentry)

        self.assertTrue(empty.get_final_content(),
                        file("tests/data/appended.db").read())
