
import datetime
import os
from xml.etree import ElementTree

from scratchlivedb.scratchdb import log
from scratchlivedb.sync import SyncBase


class SyncRhythmbox(SyncBase):
    """
    Pull music info from rhythmbox's DB.

    Currently this only does:
        - Sync inttimeadded timestamps
        - Remove missing files from scratch DB
    """
    def __init__(self, *args, **kwargs):
        SyncBase.__init__(self, *args, **kwargs)

        if not self.source:
            self.source = os.path.expanduser(
                        "~/.local/share/rhythmbox/rhythmdb.xml")
        self._db = self._parse_rhythmdb(self.source)


    ###############
    # Private API #
    ###############

    def _parse_rhythmdb(self, path):
        """
        Parse the rhythmbox db, return a dictionary of mapping
        filename->timestamp
        """
        if not os.path.exists(path):
            raise RuntimeError("Didn't find rhythmdb at %s" % path)

        db = {}
        root = ElementTree.parse(path).getroot()

        # First pass, just full out raw path and timestamp
        for child in root:
            if child.tag != "entry" or child.attrib.get("type") != "song":
                continue

            prefix = "file:///"
            location = child.find("location").text
            if not location.startswith(prefix):
                raise RuntimeError("rhythmbox location didn't start with "
                                   "expected file:/// : '%s'" % location)

            first_seen = int(child.find("first-seen").text)
            db[location[(len(prefix) - 1):]] = first_seen

        source_base_dir = self._find_shared_root(db.keys()[:])
        log.debug("Found source_base_dir=%s", source_base_dir)

        # Third pass, string source_base_dir from paths
        for key in db.keys():
            db[key[len(source_base_dir):]] = db.pop(key)

        return db


    ##############
    # Public API #
    ##############

    def sync(self, db):
        dbroot = self._find_shared_root([e.filebase for e in db.entries])

        def p(desc, key):
            print "%-20s %s" % (desc + ":", key)

        for entry in db.entries[:]:
            key = entry.filebase[len(dbroot):]
            if key not in self._db:
                p("Removing from DB", key)
                db.entries.remove(entry)
                continue

            newtime = self._db.pop(key)
            if newtime != entry.inttimeadded:
                desc = "%s %s->%s" % (key,
                        datetime.datetime.fromtimestamp(entry.inttimeadded),
                        datetime.datetime.fromtimestamp(newtime))
                p("Changing timeadded", desc)

                entry.inttimeadded = newtime

        for key, timestamp in self._db.items():
            p("Adding to DB", key)
            newentry = db.make_entry(dbroot + key)
            newentry.inttimeadded = timestamp
            db.entries.append(newentry)
