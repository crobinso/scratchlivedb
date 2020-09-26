import pytest

from . import utils


@pytest.fixture
def run_cli(capsys, monkeypatch):
    """
    Custom pytest fixture to pass a function for testing
    a bugzilla cli command.
    """
    def _do_run(*args, **kwargs):
        return utils.do_run_cli(capsys, monkeypatch, *args, **kwargs)
    return _do_run
