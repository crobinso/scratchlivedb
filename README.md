
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
a Scratch Live database file. Currently all it does is allow minimally
syncing the music library with rhythmbox, but it can easily be altered
to make one off changes.

Here's how I use it in my music org process:

- Download a bunch of music on my linux machine
- Organize it, put it into ~/Music, which is shared with my windows box
- Run rhythmbox, it picks up the new files, use rhythmbox to tweak some tags
- Mount my windows _Serato_ folder at /mnt/laptop/serato
- cd scratchlivedb.git
- ./scratchlivedb-tool --sync-rhythmbox --in-place /mnt/laptop/serato/database\ V2
- A backup library copy is stored in /mnt/laptop/serato if something went wrong
- Run 'rescan tags' in Scratch Live to pick up all the tag values

Yeah, convoluted, but for whatever reason Scratch Live likes to forget the
timestamps randomly when I sync manually on the windows machine, so everything
appears like it was added recently, which messes up how I access music.


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

* Should be straightforward to add a sync implementation that finds all the
  music in a directory and syncs it with the DB, at least superficially.

* Only tested on a linux machine

* Haven't tested setup.py except for 'test' and 'pylint' subcommands
