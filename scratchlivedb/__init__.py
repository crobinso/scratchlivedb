#!/usr/bin/python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free  Software Foundation; either version 2 of the License, or
# (at your option)  any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA.

import io
import logging
import os
import sys

from scratchlivedb.unknownentry import UnknownEntryTracker

_seen = []
log = logging.getLogger("scratchlivedb")


#################
# Debug helpers #
#################

# If we see a new file entry field in the serato database, this stuff helps
# figure out what it's purpose is.
_unknowns = UnknownEntryTracker()


def _make_unknown_str(entry, maxprint=None, dups=1):
    """
    Build a string listing some of the seen values which should
    help determine what the key actually does
    """
    if maxprint is None:
        maxprint = len(entry.values)
    keys = entry.values.keys()[:maxprint]

    try:
        valtype = _key_to_type(entry.key)
    except Exception, e:
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
    keys = _unknowns.unknowns.keys()
    keys.sort()

    if keys:
        log.warn("Unknown keys encountered: %s", keys)
        log.warn("See debug output for details")

    for key in keys:
        log.debug(_make_unknown_str(_unknowns.unknowns[key], 20, dups=20))


#####################
# Utility functions #
#####################

def _parse_cstring(content):
    """
    From the passed string, find the nearest \0 byte and return everything
    before it
    """
    ret = ""
    while True:
        char  = content.read(1)
        if char == '\0':
            break
        ret += char

    return ret


def _int2hexbin(origint, size=4):
    hexstr = "%08X" % origint
    ret = ""

    for idx in (0, 2, 4, 6)[:size]:
        idx = idx
        bytestr = hexstr[idx]
        bytestr += hexstr[idx + 1]

        ret += chr(int(bytestr, 16))
    return ret


def _hexbin2int(content):
    """
    Parse an hex string of size 'length' and convert to int
    """
    val = 0

    for idx in range(len(content)):
        c = content[idx]
        byte = ord(c)
        val += byte * ((2 ** 8) ** ((len(content) - 1) - idx))
    return val


def _make_utf16(orig):
    """
    Convert the passed string 'orig' to serato UTF16 format
    """
    new = ""
    for c in orig:
        new += "\0" + c
    return new


def _parse_utf16(data):
    """
    Convert serato utf16 format to a regular string
    """
    ret = ""
    for c in data:
        if c == "" or c == "\0":
            continue
        ret += c
    return ret


def _match_string(content, matchstr):
    """
    Make sure the value starting 'content' is 'matchstr'
    """
    readval = content.read(len(matchstr))
    if readval != matchstr:
        raise ScratchParseError("Didn't find expected string "
                "'%s', found '%s'" % (matchstr, readval))


###########################
# Class property builders #
###########################

(TYPE_STR,
 TYPE_UTFSTR,
 TYPE_INT1,
 TYPE_INT4,
 TYPE_CHAR) = range(1, 6)


def _key_to_type(key):
    if key.startswith("u"):
        return TYPE_INT4
    if key.startswith("b"):
        return TYPE_INT1
    if key.startswith("s"):
        return TYPE_CHAR
    if key.startswith("p") or key.startswith("t"):
        return TYPE_STR
    raise RuntimeError("Unknown type for key '%s'" % key)


def _get_converter(key, rawval, valtype):
    ignore = key

    if valtype == TYPE_STR:
        return rawval
    if valtype == TYPE_UTFSTR:
        return _parse_utf16(rawval)
    if valtype == TYPE_INT1:
        return ord(rawval)
    if valtype == TYPE_INT4:
        return _hexbin2int(rawval)
    if valtype == TYPE_CHAR:
        return _hexbin2int(rawval)
    raise RuntimeError("Unknown property type %s" % valtype)


def _set_field_helper(self, key, valtype, rawval):
    if valtype == TYPE_STR:
        setval = rawval
    elif valtype == TYPE_UTFSTR:
        setval = _make_utf16(rawval)
    elif valtype == TYPE_INT1:
        setval = chr(rawval)
    elif valtype == TYPE_INT4:
        setval = _int2hexbin(int(rawval))
    elif valtype == TYPE_CHAR:
        setval = _int2hexbin(int(rawval), 2)
    else:
        raise RuntimeError("Unknown property type %s" % valtype)

    # pylint: disable=W0212
    # Ignore 'Access to protected member'
    if key not in self._rawkeys:
        self._rawkeys.append(key)
    self._rawdict[key] = setval
    # pylint: enable=W0212


def _get_field_helper(self, key, valtype):
    # pylint: disable=W0212
    # Ignore 'Access to protected member'
    rawval = self._rawdict.get(key)
    # pylint: enable=W0212

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
        if _parse_cstring(content) != "vrsn":
            raise ScratchParseError("Header did not have expected prefix")
        # Strip out next \0
        _parse_cstring(content)

        _match_string(content, _make_utf16(self.version))
        _match_string(content, _make_utf16(self.type))

    def get_final_content(self):
        ret = "vrsn\0\0%s%s" % (_make_utf16(self.version),
                                _make_utf16(self.type))
        return ret


class _ScratchFileEntry(object):
    """
    Parse a track entry from a crate/database file

    First 4 characters are an ascii string describing the entry.
        only handled value is 'otrk' for a playlist track entry

    Next is 4 hex digits specifying the length of the following data

    Finally is the data of the entry, which is 'length' bytes long

    The data section is just a list of fields which have the above format.
    If the file is a crate file, each track has name==ptrk. If the
    file is the must data base, each track has name==pfil

    Other entry types:

    Boolean fields. Contain either binary 0 or 1
    bcrt :  Track is corrupt/has invalid audio data
    bmis :  Track is missing

    pdir :  file directory
    pfil :  file name for database file
    ptrk :  file name for crate file

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

    Unknown values:
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

    def __init__(self, content=None):
        self._name = None
        self._rawdata = None
        self._rawkeys = []
        self._rawdict = {}

        self._parse(content)

    filedir             = _property_helper("pdir", TYPE_UTFSTR)
    filetrack           = _property_helper("ptrk", TYPE_UTFSTR)
    filebase            = _property_helper("pfil", TYPE_UTFSTR)

    trackadded          = _property_helper("tadd", TYPE_UTFSTR)
    trackartist         = _property_helper("tart", TYPE_UTFSTR)
    trackalbum          = _property_helper("talb", TYPE_UTFSTR)
    trackbitrate        = _property_helper("tbit", TYPE_UTFSTR)
    trackbpm            = _property_helper("tbpm", TYPE_UTFSTR)
    trackcomposer       = _property_helper("tcmp", TYPE_UTFSTR)
    trackcomment        = _property_helper("tcom", TYPE_UTFSTR)
    trackcorrupt        = _property_helper("tcor", TYPE_UTFSTR)
    trackgenre          = _property_helper("tgen", TYPE_UTFSTR)
    trackgrouping       = _property_helper("tgrp", TYPE_UTFSTR)
    trackkey            = _property_helper("tkey", TYPE_UTFSTR)
    tracklabel          = _property_helper("tlbl", TYPE_UTFSTR)
    tracklength         = _property_helper("tlen", TYPE_UTFSTR)
    trackremixer        = _property_helper("trmx", TYPE_UTFSTR)
    tracktitle          = _property_helper("tsng", TYPE_UTFSTR)
    tracksize           = _property_helper("tsiz", TYPE_UTFSTR)
    tracksamplerate     = _property_helper("tsmp", TYPE_UTFSTR)
    tracktype           = _property_helper("ttyp", TYPE_UTFSTR)
    trackyear           = _property_helper("ttyr", TYPE_UTFSTR)

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
                raise RuntimeError("didn't read expected data length "
                                   "(%s != %s)" % (len(data), length))
            return name, data

        self._name, self._rawdata = parse_field(content)
        if self._name != "otrk":
            ScratchParseError("Unknown entry header '%s'" % self._name)

        datastream = io.BufferedReader(io.BytesIO(self._rawdata))
        unknowns = []
        while True:
            if datastream.peek(1) == "":
                break

            name, data = parse_field(datastream)

            if name in self._rawdict:
                raise RuntimeError("already found field for '%s'" % name)

            if name not in _seen:
                unknowns.append((name, data))

            self._rawkeys.append(name)
            self._rawdict[name] = data

        for name, data in unknowns:
            _unknowns.track_unknown(self.filebase, name, data)

    def get_final_content(self):
        field_content = ""
        for key in self._rawkeys:
            data = self._rawdict[key]
            field_content += key + _int2hexbin(len(data)) + data

        return self._name + _int2hexbin(len(field_content)) + field_content


class _ScratchFile(object):
    """
    Base class for all serato files
    """
    def __init__(self, filename, version, ftype):
        self.filename = filename
        self._content = io.BufferedReader(io.BytesIO(file(filename).read()))

        self.header = _ScratchFileHeader(self._content, version, ftype)
        self.entries = self._parse_entries()

        try:
            _log_unknowns()
        except Exception, e:
            log.debug("Error printing unknown values: %s", e)

    def _parse_entries(self):
        entries = []
        while True:
            if self._content.peek(1) == "":
                break

            entry = _ScratchFileEntry(content=self._content)
            entries.append(entry)

        return entries

    def get_final_content(self):
        entry_content = ""
        for entry in self.entries:
            entry_content += entry.get_final_content()

        return self.header.get_final_content() + entry_content


##############
# Public API #
##############

class ScratchParseError(Exception):
    pass


class ScratchCrateFile(_ScratchFile):
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
