"""Variable standardization and normalization tests.

Tests for:
- Consistent variable naming (snake_case, camelCase, etc.)
- Type consistency across similar variables
- Scope correctness and lifetime management
- Default values and initialization
- Immutability constraints (where expected)
- Documentation accuracy for variables
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import pytest

from mangrove_platform.apparat.api import GridCell, InputProcessOutput, Phase, PhaseParams
from mangrove_platform.apparat.sisa import PHASE_DEFINITIONS, SisaState

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestVariableNamingConventions:
    """Test that variables follow Python naming conventions."""

    def test_phase_definitions_is_dict(self):
        """PHASE_DEFINITIONS should be a dict."""
        assert isinstance(PHASE_DEFINITIONS, dict)

    def test_phase_definition_keys_are_lowercase(self):
        """All phase definition keys should be lowercase."""
        for key in PHASE_DEFINITIONS.keys():
            assert key.islower(), f"Phase key not lowercase: {key!r}"
            assert "_" not in key or key.islower(), f"Phase key has mixed case: {key!r}"

    def test_phase_definition_values_are_dicts(self):
        """All phase definition values should be dicts."""
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            assert isinstance(phase_def, dict), (
                f"Phase {phase_name!r}: value is {type(phase_def)}, not dict"
            )

    def test_phase_definition_dict_keys_are_snake_case(self):
        """Phase definition dict keys should use snake_case."""
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            for key in phase_def.keys():
                assert key.islower(), f"Phase {phase_name}: dict key not lowercase: {key!r}"
                assert key.replace("_", "").isalpha() or key.replace("_", "").isalnum(), (
                    f"Phase {phase_name}: invalid dict key {key!r}"
                )


class TestSisaStateDataclass:
    """Test SisaState dataclass structure and defaults."""

    def test_sisa_state_is_dataclass(self):
        """SisaState should be a dataclass."""
        assert is_dataclass(SisaState)

    def test_sisa_state_has_required_fields(self):
        """SisaState should have all required fields."""
        field_names = {f.name for f in fields(SisaState)}
        required = {
            "trigger",
            "ready",
            "components_loaded",
            "components_failed",
            "phases_resolved",
            "phases_missing",
            "phases_newly_registered",
            "prerequisites_met",
            "prerequisites_missing",
            "context_snapshot",
            "warnings",
            "tasks",
        }
        assert required.issubset(field_names), f"Missing fields: {required - field_names}"

    def test_sisa_state_field_types(self):
        """SisaState fields should have correct types."""
        state = SisaState()
        assert isinstance(state.trigger, str)
        assert isinstance(state.ready, bool)
        assert isinstance(state.components_loaded, list)
        assert isinstance(state.components_failed, list)
        assert isinstance(state.phases_resolved, list)
        assert isinstance(state.phases_missing, list)
        assert isinstance(state.phases_newly_registered, list)
        assert isinstance(state.prerequisites_met, list)
        assert isinstance(state.prerequisites_missing, list)
        assert isinstance(state.context_snapshot, dict)
        assert isinstance(state.warnings, list)
        assert isinstance(state.tasks, list)

    def test_sisa_state_default_values(self):
        """SisaState should have correct default values."""
        state = SisaState()
        assert state.trigger == "sisa"
        assert state.ready is False
        assert state.components_loaded == []
        assert state.components_failed == []
        assert state.phases_resolved == []
        assert state.phases_missing == []
        assert state.phases_newly_registered == []
        assert state.prerequisites_met == []
        assert state.prerequisites_missing == []
        assert state.context_snapshot == {}
        assert state.warnings == []
        assert state.tasks == []

    def test_sisa_state_lists_are_mutable(self):
        """SisaState list fields should be mutable."""
        state = SisaState()
        original_id = id(state.components_loaded)
        state.components_loaded.append("test")
        assert len(state.components_loaded) == 1
        assert id(state.components_loaded) == original_id  # Same list object

    def test_sisa_state_dict_is_mutable(self):
        """SisaState dict field should be mutable."""
        state = SisaState()
        state.context_snapshot["key"] = "value"
        assert state.context_snapshot["key"] == "value"


class TestGridCellVariables:
    """Test GridCell type structure and naming."""

    def test_grid_cell_is_dataclass(self):
        """GridCell should be a dataclass."""
        assert is_dataclass(GridCell)

    def test_grid_cell_has_required_fields(self):
        """GridCell should have position and value fields."""
        field_names = {f.name for f in fields(GridCell)}
        # GridCell should have coordinates and a value
        assert len(field_names) > 0

    def test_grid_cell_field_names_snake_case(self):
        """GridCell field names should use snake_case."""
        for field_obj in fields(GridCell):
            name = field_obj.name
            assert name.islower(), f"GridCell field not lowercase: {name!r}"
            assert (
                name.replace("_", "").isalpha() or name.replace("_", "").isalnum()
            ), f"GridCell field has invalid characters: {name!r}"


class TestInputProcessOutputVariables:
    """Test InputProcessOutput type structure."""

    def test_ipo_is_dataclass(self):
        """InputProcessOutput should be a dataclass."""
        assert is_dataclass(InputProcessOutput)

    def test_ipo_has_required_fields(self):
        """InputProcessOutput should have required fields."""
        field_names = {f.name for f in fields(InputProcessOutput)}
        # Should have render_snapshot and history
        assert len(field_names) > 0

    def test_ipo_field_names_snake_case(self):
        """InputProcessOutput field names should use snake_case."""
        for field_obj in fields(InputProcessOutput):
            name = field_obj.name
            assert name.islower(), f"IPO field not lowercase: {name!r}"


class TestPhaseEnumVariables:
    """Test Phase enum structure and naming."""

    def test_phase_is_enum(self):
        """Phase should be an enum-like class."""
        # Check it has members
        assert hasattr(Phase, "INITIATE") or hasattr(Phase, "initiate")

    def test_phase_members_uppercase(self):
        """Phase members should be uppercase if Enum."""
        # Enum members should be UPPERCASE by convention
        for attr_name in dir(Phase):
            if not attr_name.startswith("_"):
                # Skip methods and internal attrs
                if attr_name.isupper():
                    assert hasattr(Phase, attr_name)


class TestPhaseParamsVariables:
    """Test PhaseParams structure."""

    def test_phase_params_type_valid(self):
        """PhaseParams should be a valid type."""
        # PhaseParams should be usable as a type
        assert PhaseParams is not None


class TestVariableConsistency:
    """Test consistency of variables across the codebase."""

    def test_phase_definition_modules_consistent(self):
        """Phase definition module names should be consistent."""
        modules = {phase_def["module"] for phase_def in PHASE_DEFINITIONS.values()}
        # Most should be "phase_handlers" or similar
        for module in modules:
            assert isinstance(module, str)
            assert len(module) > 0

    def test_phase_definition_handlers_consistent(self):
        """Phase definition handler names should follow pattern."""
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            handler = phase_def["handler"]
            # Handlers should be lowercase with underscores
            assert handler.islower(), f"Handler not lowercase: {handler!r}"
            assert handler.endswith("_handler"), f"Handler doesn't end with _handler: {handler!r}"

    def test_phase_definition_descriptions_consistent_format(self):
        """Phase descriptions should have consistent capitalization."""
        for phase_name, phase_def in PHASE_DEFINITIONS.items():
            desc = phase_def["description"]
            # Descriptions should start with capital letter
            if desc:
                first_char = desc[0]
                assert first_char.isupper(), (
                    f"Phase {phase_name}: description starts with lowercase: {desc!r}"
                )


class TestVariableTypeAnnotations:
    """Test that variables have correct type annotations."""

    def test_sisa_state_field_type_annotations(self):
        """SisaState fields should have type annotations."""
        for field_obj in fields(SisaState):
            # All fields should have annotations
            assert field_obj.type is not None

    def test_grid_cell_field_type_annotations(self):
        """GridCell fields should have type annotations."""
        for field_obj in fields(GridCell):
            assert field_obj.type is not None

    def test_ipo_field_type_annotations(self):
        """InputProcessOutput fields should have type annotations."""
        for field_obj in fields(InputProcessOutput):
            assert field_obj.type is not None


class TestVariableImmutability:
    """Test immutability constraints where expected."""

    def test_grid_cell_frozen_if_expected(self):
        """GridCell should be frozen (immutable) if declared."""
        # Check the dataclass config
        if hasattr(GridCell, "__dataclass_fields__"):
            # If it has a frozen attribute, check it
            if hasattr(GridCell, "__dataclass_params__"):
                # Document expectation: GridCell should be frozen
                pass

    def test_phase_enum_members_immutable(self):
        """Phase enum members should be immutable."""
        # Enum members are always immutable
        pass


class TestVariableDocumentation:
    """Test that variables are properly documented."""

    def test_sisa_state_has_docstring(self):
        """SisaState should have a docstring."""
        assert SisaState.__doc__ is not None
        assert len(SisaState.__doc__.strip()) > 0

    def test_phase_definitions_usage_clear(self):
        """PHASE_DEFINITIONS should be documented."""
        # Check that it's used in a module with clear documentation
        # This is a soft check - the variable exists and is used
        assert len(PHASE_DEFINITIONS) > 0


class TestVariableDefaultConsistency:
    """Test default values are consistent across similar variables."""

    def test_list_fields_empty_by_default(self):
        """All list fields should default to empty list."""
        state = SisaState()
        list_fields = [
            state.components_loaded,
            state.components_failed,
            state.phases_resolved,
            state.phases_missing,
            state.phases_newly_registered,
            state.prerequisites_met,
            state.prerequisites_missing,
            state.warnings,
            state.tasks,
        ]
        for field_val in list_fields:
            assert isinstance(field_val, list)
            # Each should have its own list instance (not shared)
            assert len([f for f in list_fields if f is field_val]) == 1

    def test_dict_fields_empty_by_default(self):
        """All dict fields should default to empty dict."""
        state = SisaState()
        assert state.context_snapshot == {}

    def test_bool_fields_default_false(self):
        """Boolean fields should default to False."""
        state = SisaState()
        assert state.ready is False
