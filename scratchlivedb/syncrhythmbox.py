
import datetime
import os
from xml.etree import ElementTree

from scratchlivedb.scratchdb import log
from scratchlivedb.sync import SyncBase


class SyncRhythmbox(SyncBase):
    """
    Pull music info from rhythmbox's DB.
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

            if (child.find("hidden") is not None and
                child.find("hidden").text == "1"):
                continue

            first_seen = int(child.find("first-seen").text)
            db[location[(len(prefix) - 1):]] = first_seen

        source_base_dir = self._find_shared_root(db.keys()[:])
        log.debug("Found source_base_dir=%s", source_base_dir)

        # Third pass, strip source_base_dir from paths
        for key in db.keys():
            db[key[len(source_base_dir):]] = db.pop(key)

        return db


    ##############
    # Public API #
    ##############

    def sync(self, db, require_base=None):
        dbroot = self._find_shared_root([e.filebase for e in db.entries])
        log.debug("Found scratchlivedb base=%s", dbroot)
        if require_base is not None and dbroot != require_base:
            raise RuntimeError("Required base '%s' doesn't match detected "
                               "base '%s'" % (require_base, dbroot))

        def p(desc, key):
            print "%-20s %s" % (desc + ":", key)

        def round_to_day(ctime):
            """
            Round ctime value down to midnight, so that slight variations
            in times are all set to the same value, which helps us
            sort in scratch live
            """
            fmt = "%Y-%m-%d"
            strtime = datetime.datetime.fromtimestamp(int(ctime)).strftime(fmt)
            return int(datetime.datetime.strptime(strtime, fmt).strftime("%s"))

        rmcount = 0
        changecount = 0
        addcount = 0

        for entry in db.entries[:]:
            key = entry.filebase[len(dbroot):]
            if key not in self._db:
                p("Removing from DB", key)
                rmcount += 1
                db.entries.remove(entry)
                continue

            newtime = round_to_day(self._db.pop(key))
            if newtime != entry.inttimeadded:
                desc = "%s %s->%s" % (key,
                        datetime.datetime.fromtimestamp(entry.inttimeadded),
                        datetime.datetime.fromtimestamp(newtime))
                changecount += 1
                p("Changing timeadded", desc)

                entry.inttimeadded = newtime

        for key, timestamp in self._db.items():
            addcount += 1
            p("Adding to DB", key)
            newentry = db.make_entry(dbroot + key)
            newentry.inttimeadded = round_to_day(timestamp)
            db.entries.append(newentry)

        print
        print "Total removed: %d" % rmcount
        print "Total added:   %d" % addcount
        print "Total changed: %d" % changecount
