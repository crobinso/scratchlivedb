
scratchlivedb
-------------

scratchlivedb is a python module for reading and writing Scratch Live
database and crate files. Simple example to print the filename of every
track in the DB:

    import scratchlivedb

    db = scratchlivedb.ScratchDatabase("/path/to/my/database V2")
    for entry in db.entries:
        print entry.filebase


scratchlivedb-tool
------------------

scratchlivedb-tool is a simple tool for performing some actions on
a Scratch Live database file. Currently all it provides is a 'dump'
subcommand for printing details about the database.


Todo
----

* Crate support is limited. The format is basically:

  first entry: sort column : name=osrt,
    brev=1 (this is prob ascending/descending),
    tcvn="song" (name of the sort column)

  next entries: the visible columns : name=ovct,
    tvcn=column name, tcvw=some number, possibly  width of column

  rest of entries: name=otrk, ptrk=filename

  ScratchCrate and ScratchDatabase should be changed to not expose the
  raw entries list, probably name that to songs. ScratchCrate would
  then have a sortcolumn member and a columns member. makenew() call
  would need to handle filetrack vs. filebase difference depending
  on crate vs. db. API should be tweaked to not make it all so
  awkward.

* Only tested on a linux machine

* Extend scratchlivedb-tool 'dump' with more output options
