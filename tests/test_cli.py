
import atexit
import glob
import os

datadir = os.path.join(os.path.dirname(__file__), "data")
basicdb = os.path.join(datadir, "basic.db")
unknowndb = os.path.join(datadir, "unknown_keys.db")
rmfiles = []


def _cleanup():
    for base in rmfiles:
        for f in glob.glob(base + "*"):
            try:
                os.unlink(f)
            except Exception:
                continue


atexit.register(_cleanup)


def test_cliBasic(run_cli):
    """
    Smoke test for the CLI tool
    """
    run_cli("scratchlivedb-tool dump %s" % basicdb)


def test_cliUnknownKeys(run_cli):
    """
    Make sure unknown key detection works
    """
    # Prevent unfinished crate support from interfering
    # pylint: disable=protected-access
    # Ignore 'Access to protected member'
    from scratchlivedb.scratchdb import _unknowns
    _unknowns.unknowns = {}
    # pylint: enable=protected-access

    out = run_cli("scratchlivedb-tool dump %s" % unknowndb)
    assert "Unknown keys encountered: ['tzzz', 'uzzz', 'zzzz']" in out

    out = run_cli("scratchlivedb-tool --debug dump %s" % unknowndb)
    assert "Unknown type for key 'zzzz'" in out
