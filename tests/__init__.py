
import shlex
import sys
import StringIO


def clicomm(argv, expectfail=False):
    """
    Run bin/bugzilla.main() directly with passed argv
    """
    from tests.scriptimports import scratchlivedbtool

    argv = shlex.split(argv)

    oldstdout = sys.stdout
    oldstderr = sys.stderr
    oldstdin = sys.stdin
    oldargv = sys.argv
    try:
        out = StringIO.StringIO()
        sys.stdout = out
        sys.stderr = out
        sys.argv = argv

        ret = 0
        try:
            print " ".join(argv)
            print

            ret = scratchlivedbtool.main()
        except SystemExit, sys_e:
            ret = sys_e.code

        outt = out.getvalue()
        if outt.endswith("\n"):
            outt = outt[:-1]

        if ret != 0 and not expectfail:
            raise RuntimeError("Command failed with %d\ncmd=%s\nout=%s" %
                               (ret, argv, outt))
        elif ret == 0 and expectfail:
            raise RuntimeError("Command succeeded but we expected success\n"
                               "ret=%d\ncmd=%s\nout=%s" % (ret, argv, outt))

        return outt
    finally:
        sys.stdout = oldstdout
        sys.stderr = oldstderr
        sys.stdin = oldstdin
        sys.argv = oldargv
