import argparse
import logging
import sys

import scratchlivedb

log = logging.getLogger("scratchlivedb")
log.setLevel(logging.DEBUG)


######################
# Functional helpers #
######################

def setup_logging(debug):
    handler = logging.StreamHandler(sys.stderr)
    if debug:
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(levelname)-6s (%(module)s:%(lineno)d): %(message)s")
    else:
        handler.setLevel(logging.WARN)
        formatter = logging.Formatter("%(levelname)-6s %(message)s")

    handler.setFormatter(formatter)
    log.addHandler(handler)

    log.debug("Launched with command line: %s", " ".join(sys.argv))


###################
# main() handling #
###################

def parse_options():
    desc = "Command line tool for interacting with scratchlive databases"
    parser = argparse.ArgumentParser(description=desc)
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    parser.add_argument("scratchlivedbfile",
            help="Path to scratchlive db file ex. /path/to/database V2")
    parser.add_argument("--debug", action="store_true",
            help="Print debug output to stderr")

    dumpdesc = "Dump the database file paths"
    subparsers.add_parser("dump", description=dumpdesc)

    return parser.parse_args()


def main():
    options = parse_options()
    setup_logging(options.debug)
    dbfile = options.scratchlivedbfile
    db = scratchlivedb.ScratchDatabase(dbfile)

    if options.command == "dump":
        for entry in db.entries:
            print(entry.filebase)

    return 0
