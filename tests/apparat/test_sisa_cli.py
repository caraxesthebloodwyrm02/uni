import argparse

import pytest

from mangrove_platform.apparat.sisa import _build_arg_parser, _validate_phase_arg


def test_valid_phase():
    parser = _build_arg_parser()
    args = parser.parse_args(["-P", "highlight"])
    assert args.phase == "highlight"


def test_invalid_phase():
    parser = _build_arg_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["-P", "invalid_phase_name"])


def test_mutually_exclusive_flags():
    parser = _build_arg_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["-q", "-v"])


def test_list_phases():
    parser = _build_arg_parser()
    args = parser.parse_args(["--list-phases"])
    assert args.list_phases is True


def test_validate_phase_arg_empty():
    with pytest.raises(argparse.ArgumentTypeError, match="phase name must be non-empty"):
        _validate_phase_arg("")


def test_validate_phase_arg_invalid():
    with pytest.raises(argparse.ArgumentTypeError, match="unknown phase"):
        _validate_phase_arg("invalid_phase_name")


def test_default_arguments():
    parser = _build_arg_parser()
    args = parser.parse_args([])
    assert args.prompt == ""
    assert args.json is False
    assert args.debug is False
    assert args.quiet is False
    assert args.verbose is False
    assert args.strict is False
    assert args.phase is None
    assert args.list_phases is False


def test_debug_flag():
    parser = _build_arg_parser()
    args = parser.parse_args(["-d"])
    assert args.debug is True

    args = parser.parse_args(["--debug"])
    assert args.debug is True


def test_prompt_argument():
    parser = _build_arg_parser()
    args = parser.parse_args(["-p", "test_prompt"])
    assert args.prompt == "test_prompt"

    args = parser.parse_args(["--prompt", "test_prompt_long"])
    assert args.prompt == "test_prompt_long"


def test_json_flag():
    parser = _build_arg_parser()
    args = parser.parse_args(["-j"])
    assert args.json is True

    args = parser.parse_args(["--json"])
    assert args.json is True


def test_quiet_flag():
    parser = _build_arg_parser()
    args = parser.parse_args(["-q"])
    assert args.quiet is True

    args = parser.parse_args(["--quiet"])
    assert args.quiet is True


def test_verbose_flag():
    parser = _build_arg_parser()
    args = parser.parse_args(["-v"])
    assert args.verbose is True

    args = parser.parse_args(["--verbose"])
    assert args.verbose is True


def test_strict_flag():
    parser = _build_arg_parser()
    args = parser.parse_args(["-s"])
    assert args.strict is True

    args = parser.parse_args(["--strict"])
    assert args.strict is True
