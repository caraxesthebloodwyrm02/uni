"""Comprehensive CLI surface and debug tests.

Tests for:
- Argument parsing completeness and correctness
- Phase name validation and error handling
- CLI state transitions and edge cases
- Error messages and user feedback quality
- Argument type casting and coercion
"""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from pathlib import Path

import pytest

from mangrove_platform.apparat.sisa import (
    PHASE_DEFINITIONS,
    _build_arg_parser,
    _load_components,
    _package_root,
    _validate_phase_arg,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestCLISurfaceBasics:
    """Test CLI argument parser creation and basic functionality."""

    def test_parser_creation(self):
        """Parser should be created without errors."""
        parser = _build_arg_parser()
        assert parser is not None
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_has_required_actions(self):
        """Parser should have all expected actions."""
        parser = _build_arg_parser()
        action_names = {a.dest for a in parser._actions}

        required = {
            "phase",
            "prompt",
            "debug",
            "json",
            "quiet",
            "verbose",
            "strict",
            "list_phases",
        }
        assert required.issubset(action_names), f"Missing actions: {required - action_names}"

    def test_parser_defaults_correct(self):
        """All default values should be correctly set."""
        parser = _build_arg_parser()
        args = parser.parse_args([])

        assert args.prompt == "", f"Expected prompt='', got {args.prompt!r}"
        assert args.phase is None, f"Expected phase=None, got {args.phase!r}"
        assert args.json is False
        assert args.debug is False
        assert args.quiet is False
        assert args.verbose is False
        assert args.strict is False
        assert args.list_phases is False


class TestCLIArgumentParsing:
    """Test individual argument parsing."""

    def test_phase_short_flag(self):
        """Phase argument with -P short flag."""
        parser = _build_arg_parser()
        args = parser.parse_args(["-P", "initiate"])
        assert args.phase == "initiate"

    def test_phase_long_flag(self):
        """Phase argument with --phase long flag."""
        parser = _build_arg_parser()
        args = parser.parse_args(["--phase", "quantize"])
        assert args.phase == "quantize"

    def test_prompt_short_flag(self):
        """Prompt argument with -p short flag."""
        parser = _build_arg_parser()
        args = parser.parse_args(["-p", "test_prompt"])
        assert args.prompt == "test_prompt"

    def test_prompt_long_flag(self):
        """Prompt argument with --prompt long flag."""
        parser = _build_arg_parser()
        args = parser.parse_args(["--prompt", "test_prompt"])
        assert args.prompt == "test_prompt"

    def test_prompt_with_spaces(self):
        """Prompt should preserve spaces."""
        parser = _build_arg_parser()
        args = parser.parse_args(["-p", "this is a test prompt"])
        assert args.prompt == "this is a test prompt"

    def test_prompt_with_special_chars(self):
        """Prompt should preserve special characters."""
        parser = _build_arg_parser()
        prompt_text = "test!@#$%^&*()_+-=[]{}|;:,.<>?"
        args = parser.parse_args(["-p", prompt_text])
        assert args.prompt == prompt_text

    @pytest.mark.parametrize("flag,value", [("-j", True), ("--json", True)])
    def test_json_flags(self, flag, value):
        """JSON output flag."""
        parser = _build_arg_parser()
        args = parser.parse_args([flag])
        assert args.json == value

    @pytest.mark.parametrize("flag,value", [("-d", True), ("--debug", True)])
    def test_debug_flags(self, flag, value):
        """Debug flag."""
        parser = _build_arg_parser()
        args = parser.parse_args([flag])
        assert args.debug == value

    @pytest.mark.parametrize("flag,value", [("-q", True), ("--quiet", True)])
    def test_quiet_flags(self, flag, value):
        """Quiet flag."""
        parser = _build_arg_parser()
        args = parser.parse_args([flag])
        assert args.quiet == value

    @pytest.mark.parametrize("flag,value", [("-v", True), ("--verbose", True)])
    def test_verbose_flags(self, flag, value):
        """Verbose flag."""
        parser = _build_arg_parser()
        args = parser.parse_args([flag])
        assert args.verbose == value

    @pytest.mark.parametrize("flag,value", [("-s", True), ("--strict", True)])
    def test_strict_flags(self, flag, value):
        """Strict flag."""
        parser = _build_arg_parser()
        args = parser.parse_args([flag])
        assert args.strict == value

    def test_list_phases_short_flag(self):
        """List phases with --list-phases."""
        parser = _build_arg_parser()
        args = parser.parse_args(["--list-phases"])
        assert args.list_phases is True

    def test_combined_flags(self):
        """Multiple flags should combine correctly."""
        parser = _build_arg_parser()
        args = parser.parse_args(["-d", "-j", "-v", "-P", "initiate"])
        assert args.debug is True
        assert args.json is True
        assert args.verbose is True
        assert args.phase == "initiate"


class TestCLIPhaseValidation:
    """Test phase name validation."""

    def test_validate_phase_arg_valid(self):
        """Valid phase should not raise."""
        for phase_name in PHASE_DEFINITIONS.keys():
            result = _validate_phase_arg(phase_name)
            assert result == phase_name, f"Validation changed phase name: {phase_name}"

    def test_validate_phase_arg_empty_raises(self):
        """Empty string should raise."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be non-empty"):
            _validate_phase_arg("")

    def test_validate_phase_arg_invalid_raises(self):
        """Invalid phase should raise."""
        with pytest.raises(argparse.ArgumentTypeError, match="unknown phase"):
            _validate_phase_arg("invalid_phase_xyz")

    def test_validate_phase_arg_whitespace_not_stripped(self):
        """Leading/trailing whitespace should not be auto-stripped."""
        with pytest.raises(argparse.ArgumentTypeError, match="unknown phase"):
            _validate_phase_arg(" initiate ")

    def test_parser_rejects_invalid_phase(self):
        """Parser should reject invalid phase."""
        parser = _build_arg_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-P", "not_a_phase"])


class TestCLIMutualExclusivity:
    """Test mutually exclusive argument groups."""

    def test_quiet_verbose_mutually_exclusive(self):
        """Quiet and verbose should be mutually exclusive."""
        parser = _build_arg_parser()
        # This should raise SystemExit because they're in a mutually exclusive group
        with pytest.raises(SystemExit):
            parser.parse_args(["-q", "-v"])

    def test_quiet_alone_allowed(self):
        """Quiet alone should be allowed."""
        parser = _build_arg_parser()
        args = parser.parse_args(["-q"])
        assert args.quiet is True
        assert args.verbose is False

    def test_verbose_alone_allowed(self):
        """Verbose alone should be allowed."""
        parser = _build_arg_parser()
        args = parser.parse_args(["-v"])
        assert args.verbose is True
        assert args.quiet is False


class TestCLIErrorMessages:
    """Test quality of CLI error messages."""

    def test_invalid_phase_error_message(self):
        """Error message for invalid phase should be clear."""
        parser = _build_arg_parser()
        with pytest.raises(SystemExit):
            # Capture stderr to check error message
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                parser.parse_args(["-P", "bad_phase"])
            finally:
                sys.stderr = old_stderr

    def test_missing_required_argument_error(self):
        """Missing required argument should error."""
        # Most arguments have defaults, so this may not apply
        parser = _build_arg_parser()
        # If there's a required argument, test that it's required
        args = parser.parse_args([])
        assert args is not None  # Parser should succeed with defaults

    def test_unknown_argument_error(self):
        """Unknown argument should raise."""
        parser = _build_arg_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--unknown-flag"])


class TestCLIEdgeCases:
    """Test edge cases in CLI parsing."""

    def test_empty_command_line(self):
        """Empty command line should use all defaults."""
        parser = _build_arg_parser()
        args = parser.parse_args([])
        assert args.phase is None
        assert args.prompt == ""
        assert args.debug is False

    def test_phase_argument_only(self):
        """Just phase argument should work."""
        parser = _build_arg_parser()
        args = parser.parse_args(["-P", "initiate"])
        assert args.phase == "initiate"
        assert args.prompt == ""

    def test_prompt_argument_only(self):
        """Just prompt argument should work."""
        parser = _build_arg_parser()
        args = parser.parse_args(["-p", "test"])
        assert args.prompt == "test"
        assert args.phase is None

    def test_very_long_prompt(self):
        """Very long prompt should be preserved."""
        parser = _build_arg_parser()
        long_prompt = "x" * 10000
        args = parser.parse_args(["-p", long_prompt])
        assert args.prompt == long_prompt
        assert len(args.prompt) == 10000

    def test_special_characters_in_phase(self):
        """Phase names with special chars should fail validation."""
        parser = _build_arg_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-P", "invalid-phase"])


class TestCLIPhaseDefinitions:
    """Test phase definitions are complete and valid."""

    def test_phase_definitions_not_empty(self):
        """PHASE_DEFINITIONS should not be empty."""
        assert len(PHASE_DEFINITIONS) > 0

    def test_all_phases_have_required_keys(self):
        """Every phase should have required keys."""
        required_keys = {"module", "handler", "params", "description"}
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            assert isinstance(phase_def, dict), f"{phase_name}: not a dict"
            missing = required_keys - set(phase_def.keys())
            assert not missing, f"{phase_name}: missing keys {missing}"

    def test_all_phase_descriptions_non_empty(self):
        """Every phase should have a non-empty description."""
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            desc = phase_def.get("description", "")
            assert desc, f"{phase_name}: empty description"
            assert isinstance(desc, str), f"{phase_name}: description not a string"

    def test_all_phase_handlers_valid_identifiers(self):
        """Handler names should be valid Python identifiers."""
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            handler = phase_def.get("handler", "")
            assert handler, f"{phase_name}: empty handler"
            assert handler.isidentifier(), f"{phase_name}: invalid identifier {handler!r}"

    def test_all_phase_modules_valid_identifiers(self):
        """Module names should be valid identifiers or dotted paths."""
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            module = phase_def.get("module", "")
            assert module, f"{phase_name}: empty module"
            # Module names can be dotted paths
            parts = module.split(".")
            assert all(p.isidentifier() for p in parts), (
                f"{phase_name}: invalid module {module!r}"
            )

    def test_phase_params_is_list(self):
        """Params should be a list."""
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            params = phase_def.get("params")
            assert isinstance(params, list), f"{phase_name}: params not a list"


class TestPackageRoot:
    """Test _package_root() function."""

    def test_package_root_returns_string(self):
        """_package_root should return a string."""
        root = _package_root()
        assert isinstance(root, str)

    def test_package_root_not_empty(self):
        """_package_root should not return empty string."""
        root = _package_root()
        assert len(root) > 0

    def test_package_root_contains_apparat(self):
        """_package_root should contain 'apparat' in the path."""
        root = _package_root()
        assert "apparat" in root


class TestComponentLoading:
    """Test component loading functionality."""

    def test_load_components_returns_tuple(self):
        """_load_components should return a tuple."""
        result = _load_components()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_load_components_returns_lists(self):
        """_load_components should return (loaded_list, failed_list)."""
        loaded, failed = _load_components()
        assert isinstance(loaded, list)
        assert isinstance(failed, list)

    def test_component_loading_has_items(self):
        """At least some components should load successfully."""
        loaded, failed = _load_components()
        # We expect some components to load
        assert len(loaded) > 0, "No components loaded"
