
import io
import logging
import os
import time

from scratchlivedb.unknownentry import UnknownEntryTracker

_seen = []
log = logging.getLogger("scratchlivedb")
log.addHandler(logging.NullHandler())


#################
# Debug helpers #
#################

# If we see a new file entry field in the serato database, this stuff helps
# figure out what it's purpose is.
_unknowns = UnknownEntryTracker()


def _make_unknown_str(entry):
    """
    Build a string listing some of the seen values which should
    help determine what the key actually does
    """
    maxprint = 20
    dups = 20
    keys = list(entry.values.keys())[:maxprint]

    try:
        valtype = _unknown_key_to_type(entry.key)
    except Exception as e:
        log.debug(e)
        valtype = None

    ret = "Unknown type: %s\n" % entry.key
    for val in keys:
        files = sorted(entry.values[val])
        msg = ""
        idx = 0
        for idx in range(min(len(files), dups)):
            f = str(files[idx])
            if msg:
                msg += "\n"
            msg += "  %-45s" % f[-min(len(f), 45):]

        if valtype is not None:
            converted_val = _get_converter(entry.key, val, valtype)
        else:
            converted_val = repr(val)

        msg += " %-20s : %s" % ("(and %s others)" % (len(files) - idx - 1),
                                converted_val)
        ret += msg + "\n"

    return ret + "\n"


def _log_unknowns():
    keys = list(_unknowns.unknowns.keys())
    keys.sort()

    if keys:
        log.warning("Unknown keys encountered: %s", keys)
        log.warning("See debug output for details")

    for key in keys:
        log.debug(_make_unknown_str(_unknowns.unknowns[key]))


#####################
# Utility functions #
#####################

def _parse_cstring(content):
    """
    From the passed string, find the nearest \0 byte and return everything
    before it
    """
    ret = b""
    while True:
        char = content.read(1)
        if char == b'\0':
            break
        ret += char

    return ret


def _int2hexbin(origint):
    """
    Convert the passed integer into a 4 byte binary hex string
    """
    return origint.to_bytes(4, "big")


def _hexbin2int(bytedata):
    """
    Convert the passed hex binary string into its interger value
    """
    val = 0

    for idx, byte in enumerate(bytedata):
        val += byte * ((2 ** 8) ** ((len(bytedata) - 1) - idx))
    return val


def _str_to_slstr(orig):
    """
    Convert the passed string 'orig' to serato format
    """
    return orig.encode("utf-16-be")


def _parse_slstr(bytedata):
    """
    Convert serato string format to a regular string. The format is
    an array of 32bit integers representing unicode code points.
    """
    return bytedata.decode("utf-16-be")


def _match_string(content, matchstr):
    """
    Make sure the value starting 'content' is 'matchstr'
    """
    readval = content.read(len(matchstr))
    if readval != matchstr:
        raise ScratchParseError(  # pragma: no cover
                "Didn't find expected string "
                "'%s', found '%s'" % (matchstr, readval))


###########################
# Class property builders #
###########################

(TYPE_UTF16,
 TYPE_INT1,
 TYPE_INT4,
 TYPE_CHAR) = list(range(1, 5))


def _unknown_key_to_type(key):
    if key.startswith("u"):
        return TYPE_INT4
    if key.startswith("b"):
        return TYPE_INT1
    if key.startswith("s"):
        return TYPE_CHAR  # pragma: no cover
    if key.startswith("p") or key.startswith("t"):
        return TYPE_UTF16
    raise RuntimeError("Unknown type for key '%s'" % key)


def _get_converter(_key, rawval, valtype):
    if valtype == TYPE_UTF16:
        return _parse_slstr(rawval)
    if valtype == TYPE_INT1:
        return ord(rawval)
    if valtype == TYPE_INT4:
        return _hexbin2int(rawval)
    if valtype == TYPE_CHAR:
        return _hexbin2int(rawval)
    raise RuntimeError(  # pragma: no cover
            "Unknown property type %s" % valtype)


def _set_field_helper(self, key, valtype, rawval):
    if valtype == TYPE_UTF16:
        setval = _str_to_slstr(rawval)
    elif valtype == TYPE_INT4:
        setval = _int2hexbin(int(rawval))
    elif valtype == TYPE_CHAR:
        setval = _int2hexbin(int(rawval))[-2:]
    elif valtype == TYPE_INT1:
        setval = _int2hexbin(int(rawval))[-1:]
    else:
        raise RuntimeError(  # pragma: no cover
                "Unknown property type %s" % valtype)

    # pylint: disable=protected-access
    # Ignore 'Access to protected member'
    if key not in self._rawkeys:
        self._rawkeys.append(key)
    self._rawdict[key] = setval
    # pylint: enable=protected-access


def _get_field_helper(self, key, valtype):
    # pylint: disable=protected-access
    # Ignore 'Access to protected member'
    rawval = self._rawdict.get(key)
    # pylint: enable=protected-access

    if rawval is None:
        return None

    return _get_converter(key, rawval, valtype)


def _property_helper(key, valtype):
    if key not in _seen:
        _seen.append(key)
    getter = lambda self: _get_field_helper(self, key, valtype)
    setter = lambda self, val: _set_field_helper(self, key, valtype, val)

    return property(getter, setter)


###################
# Private classes #
###################

class _ScratchFileHeader(object):
    """
    Parse file header format. Basically is

    vrsn\0\0%(version)s\0%(type)s\0
    """
    def __init__(self, content, version, ftype):
        self.version = version
        self.type = ftype

        self._parse(content)

    def _parse(self, content):
        if _parse_cstring(content) != b"vrsn":
            raise ScratchParseError(  # pragma: no cover
                    "Header did not have expected prefix")
        # Strip out next \0
        _parse_cstring(content)

        _match_string(content, _str_to_slstr(self.version))
        _match_string(content, _str_to_slstr(self.type))

    def get_final_content(self):
        ret = b"vrsn\0\0%s%s" % (_str_to_slstr(self.version),
                                 _str_to_slstr(self.type))
        return ret


class _ScratchFileEntry(object):
    """
    Parse a track entry from a crate/database file

    First 4 characters are an ascii string describing the entry.
        only handled value is 'otrk' for a playlist track entry

    Next is 4 hex digits specifying the length of the following data

    Finally is the data of the entry, which is 'length' bytes long

    The data section is just a list of fields which have the above format.
    The known fields are:

    # boolean fields, contain either binary 0 or 1
    bcrt :  Track is corrupt/has invalid audio data
    bmis :  Track is missing

    # path fields, stored as utf-16-be strings
    pdir :  file directory
    pfil :  file name for database file
    ptrk :  file name for crate file

    # string fields
    tadd :  track date added
    talb :  track album name
    tart :  track artist
    tbit :  track bitrate
    tbpm :  track bpm
    tcmp :  track composer
    tcom :  track comment
    tcor :  track is corrupt, a string desc of the problem
    tgen :  track genre
    tgrp :  track grouping
    tkey :  track musical key
    tlbl :  track release label
    tlen :  track length
    trmx :  track remixer
    tsiz :  track size
    tsmp :  track sample rate
    tsng :  track song name
    ttyp :  track type (mp3, wav, etc.)
    ttyr :  track year

    # 4 digit integers
    uadd :  time added. value is 32bit ctime
    udsc :  Disc number
    ufsb :  File size in bytes
    ulbl :  Label color of the track in serato. Seems to be a rgb mask, format
                0RGB.
    utkn :  Track number

    # Unknown values:
    bbgl :  UNKNOWN: All tracks are 0
    bhrt :  UNKNOWN: All tracks are 1, except missing tracks are 0. Like blop
    blop :  UNKNOWN: All tracks are 0, except missing tracks are 1. Like bhrt

    bovc :  UNKNOWN: See bply
    bply :  UNKNOWN: Kinda close to bovc. At time of writing, of 6000 tracks
                     about 1500 had bply and 2000 had bovc. I think bply is
                     whether track is shown in green in serato and bovc is
                     whether it's ever been played, but not sure what
                     determines the difference.

    biro :  UNKNOWN: all my tracks are 0
    bitu :  UNKNOWN: all my tracks are 0
    buns :  UNKNOWN: all my tracks are 0
    bwlb :  UNKNOWN: all my tracks are 0
    bwll :  UNKNOWN: all my tracks are 0
    sbav :  UNKNOWN: Something to do with serato tags in the MP3 file. Most
                     files are just 0
    utme :  UNKNOWN: Some ctime value, couldn't match it to anything though

    """

    def __init__(self, content=None, filename=None):
        self._name = None
        self._rawdata = None
        self._rawkeys = []
        self._rawdict = {}

        if content is not None:
            self._parse(content)
        elif filename is not None:
            self._set_stub_from_file(filename)
        else:
            raise RuntimeError(  # pragma: no cover
                    "content or filename must be specified")


    filedir             = _property_helper("pdir", TYPE_UTF16)
    filetrack           = _property_helper("ptrk", TYPE_UTF16)
    filebase            = _property_helper("pfil", TYPE_UTF16)

    trackadded          = _property_helper("tadd", TYPE_UTF16)
    trackartist         = _property_helper("tart", TYPE_UTF16)
    trackalbum          = _property_helper("talb", TYPE_UTF16)
    trackbitrate        = _property_helper("tbit", TYPE_UTF16)
    trackbpm            = _property_helper("tbpm", TYPE_UTF16)
    trackcomposer       = _property_helper("tcmp", TYPE_UTF16)
    trackcomment        = _property_helper("tcom", TYPE_UTF16)
    trackcorrupt        = _property_helper("tcor", TYPE_UTF16)
    trackgenre          = _property_helper("tgen", TYPE_UTF16)
    trackgrouping       = _property_helper("tgrp", TYPE_UTF16)
    trackkey            = _property_helper("tkey", TYPE_UTF16)
    tracklabel          = _property_helper("tlbl", TYPE_UTF16)
    tracklength         = _property_helper("tlen", TYPE_UTF16)
    trackremixer        = _property_helper("trmx", TYPE_UTF16)
    tracktitle          = _property_helper("tsng", TYPE_UTF16)
    tracksize           = _property_helper("tsiz", TYPE_UTF16)
    tracksamplerate     = _property_helper("tsmp", TYPE_UTF16)
    tracktype           = _property_helper("ttyp", TYPE_UTF16)
    trackyear           = _property_helper("ttyr", TYPE_UTF16)

    boolmissing         = _property_helper("bmis", TYPE_INT1)
    boolcorrupt         = _property_helper("bcrt", TYPE_INT1)

    inttimeadded        = _property_helper("uadd", TYPE_INT4)
    inttracknum         = _property_helper("utkn", TYPE_INT4)
    intcolor            = _property_helper("ulbl", TYPE_INT4)
    intfilesize         = _property_helper("ufsb", TYPE_INT4)
    intdisknum          = _property_helper("udsc", TYPE_INT4)
    inttimemodified     = _property_helper("utme", TYPE_INT4)

    # Unknown properties
    bbgl                = _property_helper("bbgl", TYPE_INT1)
    bhrt                = _property_helper("bhrt", TYPE_INT1)
    biro                = _property_helper("biro", TYPE_INT1)
    bitu                = _property_helper("bitu", TYPE_INT1)
    buns                = _property_helper("buns", TYPE_INT1)
    bwlb                = _property_helper("bwlb", TYPE_INT1)
    bwll                = _property_helper("bwll", TYPE_INT1)
    blop                = _property_helper("blop", TYPE_INT1)
    bovc                = _property_helper("bovc", TYPE_INT1)
    bply                = _property_helper("bply", TYPE_INT1)
    sbav                = _property_helper("sbav", TYPE_CHAR)

    def _parse(self, content):
        def parse_field(c):
            name = c.read(4)
            rawlen = c.read(4)
            length = _hexbin2int(rawlen)
            data = c.read(length)
            if len(data) != length:
                raise RuntimeError(  # pragma: no cover
                        "didn't read expected data length "
                        "(%s != %s)" % (len(data), length))
            return name.decode("utf-8"), data

        self._name, self._rawdata = parse_field(content)
        if self._name != "otrk":
            ScratchParseError("Unknown entry header '%s'" % self._name)

        datastream = io.BufferedReader(io.BytesIO(self._rawdata))
        unknowns = []
        while True:
            if not datastream.peek(1):
                break

            name, data = parse_field(datastream)

            if name in self._rawdict:
                raise RuntimeError(  # pragma: no cover
                        "already found field for '%s'" % name)

            if name not in _seen:
                unknowns.append((name, data))

            self._rawkeys.append(name)
            self._rawdict[name] = data

        for name, data in unknowns:
            _unknowns.track_unknown(self.filebase, name, data)

    def _set_stub_from_file(self, filename):
        self._name = "otrk"

        # Scratch Live obviously supports other formats, but I haven't
        # tested any. Rather explicitly error than just wing it and have
        # things silently fail
        extension_list = ["mp3"]
        ext = os.path.splitext(filename)[1].lower().strip(".")
        if ext not in extension_list:
            log.warning("%s extension '%s' not in tested extension list %s",
                     filename, ext, extension_list)
            if not ext:
                log.debug("No file extension, assuming mp3")
                ext = "mp3"

        # This is the minimum required to get the file to appear in
        # Scratch Live UI, 'rescan tags' will fill in the rest.
        # And order is important, at least tracktype needs to be first!
        self.tracktype = ext
        self.inttimeadded = int(time.time())
        self.inttimemodified = int(time.time())
        self.filebase = filename


    ##############
    # Public API #
    ##############

    def get_final_content(self):
        field_content = b""
        for key in self._rawkeys:
            data = self._rawdict[key]
            field_content += key.encode("utf-8")
            field_content += _int2hexbin(len(data))
            field_content += data

        ret = b""
        ret += self._name.encode("utf-8")
        ret += _int2hexbin(len(field_content))
        ret += field_content
        return ret


class _ScratchFile(object):
    """
    Base class for all serato files
    """

    @staticmethod
    def make_entry(filename):
        return _ScratchFileEntry(filename=filename)

    def __init__(self, filename, version, ftype):
        self.filename = filename
        self._content = io.BufferedReader(
                io.BytesIO(open(filename, "rb").read()))

        self.header = _ScratchFileHeader(self._content, version, ftype)
        self.entries = self._parse_entries()

        try:
            _log_unknowns()
        except Exception as e:
            log.debug("Error printing unknown values: %s", e)

    def _parse_entries(self):
        entries = []
        while True:
            if not self._content.peek(1):
                break

            entry = _ScratchFileEntry(content=self._content)
            entries.append(entry)

        return entries

    def get_final_content(self):
        entry_content = b""
        for entry in self.entries:
            entry_content += entry.get_final_content()

        ret = b""
        ret += self.header.get_final_content()
        ret += entry_content
        return ret


##############
# Public API #
##############

class ScratchParseError(Exception):
    pass


class ScratchCrate(_ScratchFile):
    """
    Represents a serato crate file
    """
    def __init__(self, filename):
        _ScratchFile.__init__(self, filename,
                            "81.0", "/Serato ScratchLive Crate")


class ScratchDatabase(_ScratchFile):
    """
    Represents a "database V2" serato file, which contains the music
    library info
    """
    def __init__(self, filename):
        _ScratchFile.__init__(self, filename,
                            "@2.0", "/Serato Scratch LIVE Database")
