"""Test command-line interface."""

from contextlib import suppress
from __init__ import __version__
from config.cli import parse_arguments

def test_common(capsys):
    """Test --debug and --version."""
    args = parse_arguments(["--debug", "apt", "bar"])
    assert args.debug is True
    args = parse_arguments(["apt", "--debug", "bar"])
    assert args.debug is True
    args = parse_arguments(["apt", "bar", "--debug"])
    assert args.debug is True
    args = parse_arguments(["apt", "bar"])
    assert args.debug is False

    with suppress(SystemExit):
        for args in [["--version"],
                     ["--version", "apt", "bar"],
                     ["apt", "--version", "bar"],
                     ["apt", "bar", "--version"]]:
            args = parse_arguments(args)
            out, err = capsys.readouterr()
            assert out == __version__
