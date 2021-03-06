import os

import scratchlivedb

datadir = os.path.join(os.path.dirname(__file__), "data")
basicdb = os.path.join(datadir, "basic.db")
emptydb = os.path.join(datadir, "empty.db")



def test_dbNoChangeBasic():
    """
    Parse and resave the DB, make sure it doesn't change
    """
    db = scratchlivedb.ScratchDatabase(basicdb)
    assert db.get_final_content() == open(basicdb, "rb").read()


def test_dbNoChangeProperties():
    """
    Set every property with it's original value, ensure there's no change
    """
    db = scratchlivedb.ScratchDatabase(basicdb)

    def _get_properties(obj):
        ret = []
        for p in dir(obj.__class__):
            if type(getattr(obj.__class__, p)) == property:
                ret.append(p)
        return ret

    for entry in db.entries:
        for propname in _get_properties(entry):
            val = getattr(entry, propname)
            if val is None:
                continue
            setattr(entry, propname, val)

    assert db.get_final_content() == open(basicdb, "rb").read()


def test_dbEmptyDB():
    """
    Empty the DB, compare it, make sure it parses correctly
    """
    db = scratchlivedb.ScratchDatabase(basicdb)
    empty = scratchlivedb.ScratchDatabase(emptydb)
    rawempty = open(emptydb, "rb").read()

    db.entries = []
    assert db.get_final_content() == rawempty
    assert empty.get_final_content() == rawempty


def test_dbDBDocString():
    """
    This is a weird one, but it's for my own sanity. Make sure
    the DB doc string and DB properties are in sync.
    """
    db = scratchlivedb.ScratchDatabase(basicdb)
    doc = db.entries[0].__doc__

    # pylint: disable=protected-access
    # Ignore 'Access to protected member'
    rawkeys = scratchlivedb.scratchdb._seen[:]
    # pylint: enable=protected-access

    dockeys = []
    for line in doc.splitlines():
        line = line.strip("\n").strip()
        if line[4:6] != " :":
            continue
        dockeys.append(line.split(" :")[0])

    dockeys.sort()
    rawkeys.sort()
    assert dockeys == rawkeys


def test_dbNonAscii():
    """
    Test formatting non-ASCII filenames
    """
    empty = scratchlivedb.ScratchDatabase(emptydb)

    # pylint: disable=line-too-long
    # pylint: disable=protected-access

    # Some basic unicode test
    name = """Users/powermac/Music/Jîcksons -#- Bléme It ün the Boogie (12" Single Version) kopie.mp3"""
    rawname = b"""\x00U\x00s\x00e\x00r\x00s\x00/\x00p\x00o\x00w\x00e\x00r\x00m\x00a\x00c\x00/\x00M\x00u\x00s\x00i\x00c\x00/\x00J\x00\xee\x00c\x00k\x00s\x00o\x00n\x00s\x00 \x00-\x00#\x00-\x00 \x00B\x00l\x00\xe9\x00m\x00e\x00 \x00I\x00t\x00 \x00\xfc\x00n\x00 \x00t\x00h\x00e\x00 \x00B\x00o\x00o\x00g\x00i\x00e\x00 \x00(\x001\x002\x00"\x00 \x00S\x00i\x00n\x00g\x00l\x00e\x00 \x00V\x00e\x00r\x00s\x00i\x00o\x00n\x00)\x00 \x00k\x00o\x00p\x00i\x00e\x00.\x00m\x00p\x003"""

    entry = empty.make_entry(name)
    assert entry.filebase == name
    assert entry._rawdict["pfil"] == rawname

    # Multibyte unicode test
    name = """Users/powermac/Music/Jîcksons -#- Bléme It ün the Ā and ā. (ïé´´êøo12" Single Version) kopie.mp3"""
    rawname = b"""\x00U\x00s\x00e\x00r\x00s\x00/\x00p\x00o\x00w\x00e\x00r\x00m\x00a\x00c\x00/\x00M\x00u\x00s\x00i\x00c\x00/\x00J\x00\xee\x00c\x00k\x00s\x00o\x00n\x00s\x00 \x00-\x00#\x00-\x00 \x00B\x00l\x00\xe9\x00m\x00e\x00 \x00I\x00t\x00 \x00\xfc\x00n\x00 \x00t\x00h\x00e\x00 \x01\x00\x00 \x00a\x00n\x00d\x00 \x01\x01\x00.\x00 \x00(\x00\xef\x00\xe9\x00\xb4\x00\xb4\x00\xea\x00\xf8\x00o\x001\x002\x00"\x00 \x00S\x00i\x00n\x00g\x00l\x00e\x00 \x00V\x00e\x00r\x00s\x00i\x00o\x00n\x00)\x00 \x00k\x00o\x00p\x00i\x00e\x00.\x00m\x00p\x003"""

    entry = empty.make_entry(name)
    assert entry.filebase == name
    assert entry._rawdict["pfil"] == rawname


def test_dbAddToDB():
    """
    Test adding entries to a DB
    """
    basic = scratchlivedb.ScratchDatabase(basicdb)
    empty = scratchlivedb.ScratchDatabase(emptydb)

    empty.entries.append(basic.entries[10])
    empty.entries.append(basic.entries[20])

    newentry = empty.make_entry("foo/some/file/path")
    newentry.tracktitle = "Hey a track title"
    newentry.inttimeadded = 1335865095
    newentry.inttimemodified = 1335865095
    empty.entries.append(newentry)

    final = empty.get_final_content()
    appended_db = open("tests/data/appended.db", "rb").read()
    assert final == appended_db
