
import shlex
import sys


def do_run_cli(capsys, monkeypatch, argvstr, expectfail=False):
    """
    Run cli main() directly with passed argv
    """
    argv = shlex.split(argvstr)
    monkeypatch.setattr(sys, "argv", argv)

    from scratchlivedb import _cli

    ret = 0
    try:
        _cli.main()
    except SystemExit as sys_e:
        ret = sys_e.code

    out, err = capsys.readouterr()
    outstr = out + err

    if ret != 0 and not expectfail:
        raise RuntimeError("Command failed with %d\ncmd=%s\nout=%s" %
                           (ret, argvstr, outstr))
    if ret == 0 and expectfail:
        raise RuntimeError("Command succeeded but we expected success\n"
                           "ret=%d\ncmd=%s\nout=%s" %
                           (ret, argvstr, outstr))
    return outstr
