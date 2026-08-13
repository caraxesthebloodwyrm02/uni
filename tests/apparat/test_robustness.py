import pytest

from mangrove_platform.apparat.api import ApparatValidationError
from mangrove_platform.apparat.apparat import register_phase_handler
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor


def test_invalid_syntax():
    """Test that phase strings failing the regex raise ApparatValidationError."""
    processor = HorizontalTextureProcessor(10, 10)
    # These target the shared PHASE_STEP_PATTERN from phase_validation.
    invalid_phases = ["!!!", ":arg1", " phase:arg1", "phase name:arg1", "phase:arg1 arg2"]
    for phase in invalid_phases:
        with pytest.raises(ApparatValidationError, match="Invalid phase syntax"):
            processor.process_phase(phase)


def test_registry_misses():
    """Test that phase names not in PHASE_REGISTRY raise ApparatValidationError."""
    processor = HorizontalTextureProcessor(10, 10)
    for phase in ("non_existent_phase", "nonexistent_phase:arg1", "123:arg"):
        with pytest.raises(ApparatValidationError, match="not found in registry"):
            processor.process_phase(phase)


def test_parameter_count_too_many():
    """Test that providing more arguments than the signature defines raises ApparatValidationError."""
    processor = HorizontalTextureProcessor(10, 10)
    # 'scale' expects 1 parameter ('factor')
    with pytest.raises(ApparatValidationError, match="Unexpected parameters for phase 'scale'"):
        processor.process_phase("scale:1.0,2.0")


def test_parameter_count_too_few():
    """Test that providing fewer arguments than the signature requires raises ApparatValidationError."""
    processor = HorizontalTextureProcessor(10, 10)
    # 'clamp' expects 2 parameters ('min_val', 'max_val')
    with pytest.raises(
        ApparatValidationError,
        match="Parameter validation error for phase clamp: Missing required parameter 'max_val'",
    ):
        processor.process_phase("clamp:0.1")


def test_type_mismatch():
    """Test that arguments that cannot be cast to the signature type raise ApparatValidationError."""
    processor = HorizontalTextureProcessor(10, 10)
    # 'scale' expects a float for 'factor'
    with pytest.raises(
        ApparatValidationError,
        match="Parameter validation error for phase scale: Parameter 'factor' for phase 'scale' must be of type float",
    ):
        processor.process_phase("scale:abc")


def test_chaos_handler():
    """
    Test that unexpected exceptions in handlers are wrapped in ApparatValidationError
    and do not leak the original traceback as the primary exception.
    """

    # Register a chaos handler
    def chaos_handler(processor, params):
        chaos_type = params.get("type")
        if chaos_type == "runtime":
            raise RuntimeError("Chaos RuntimeError!")
        elif chaos_type == "attribute":
            raise AttributeError("Chaos AttributeError!")
        elif chaos_type == "zero":
            raise ZeroDivisionError("Chaos ZeroDivisionError!")
        return []

    # Use the registry helper
    # We can't use the decorator here easily because it's inside a test function,
    # so we call the registration function directly.
    register_phase_handler("chaos_handler", signature={"type": str}, param_map=["type"])(
        chaos_handler
    )

    processor = HorizontalTextureProcessor(10, 10)

    test_cases = [
        (
            "chaos_handler:runtime",
            "Unexpected error executing phase chaos_handler: Chaos RuntimeError!",
        ),
        (
            "chaos_handler:attribute",
            "Unexpected error executing phase chaos_handler: Chaos AttributeError!",
        ),
        (
            "chaos_handler:zero",
            "Unexpected error executing phase chaos_handler: Chaos ZeroDivisionError!",
        ),
    ]

    for phase_call, expected_msg in test_cases:
        with pytest.raises(ApparatValidationError) as exc_info:
            processor.process_phase(phase_call)
        assert expected_msg in str(exc_info.value)
        # Ensure it's not the original exception (it's wrapped)
        assert not isinstance(exc_info.value, (RuntimeError, AttributeError, ZeroDivisionError))


def test_apparat_validation_error_propagation():
    """Test that ApparatValidationError raised inside a handler propagates unwrapped."""

    def error_handler(processor, params):
        raise ApparatValidationError("Direct validation error")

    register_phase_handler("error_handler", signature={})(error_handler)
    processor = HorizontalTextureProcessor(10, 10)
    with pytest.raises(ApparatValidationError, match="^Direct validation error$"):
        processor.process_phase("error_handler")


def test_none_signature_handler():
    """Test that handlers registered with signature=None bypass parameter validation."""

    def dynamic_handler(processor, params):
        # It should receive raw params mapped according to param_map
        assert params == {"a": "val1", "b": "val2"}
        return []

    register_phase_handler("dynamic_handler", signature=None, param_map=["a", "b"])(dynamic_handler)
    processor = HorizontalTextureProcessor(10, 10)
    result = processor.process_phase("dynamic_handler:val1,val2")
    assert result == []


def test_type_error_casting():
    """Test that TypeError raised during parameter casting raises ApparatValidationError."""

    def type_raiser(val):
        raise TypeError("Forced TypeError during cast")

    def custom_type_handler(processor, params):
        return []

    register_phase_handler("custom_type", signature={"param": type_raiser}, param_map=["param"])(
        custom_type_handler
    )
    processor = HorizontalTextureProcessor(10, 10)
    with pytest.raises(
        ApparatValidationError,
        match="Parameter validation error for phase custom_type: Parameter 'param' for phase 'custom_type' must be of type type_raiser",
    ):
        processor.process_phase("custom_type:val")


def test_scale_highlight_failure_suppression():
    """Test that an exception in the secondary highlight handler during scale is suppressed."""
    from mangrove_platform.apparat.api import GridCell
    from mangrove_platform.apparat.apparat import PHASE_REGISTRY

    # Temporarily replace highlight handler with one that raises Exception
    original = PHASE_REGISTRY.get("highlight")

    def failing_highlight(processor, params):
        raise RuntimeError("Highlight failed")

    PHASE_REGISTRY["highlight"] = (failing_highlight, {}, [])
    try:
        processor = HorizontalTextureProcessor(2, 2)
        processor.ipo.input_data = [GridCell(0, 0, 10.0, "acoustic")]
        # Should not raise exception even though highlight raises Exception
        result = processor.process_phase("scale:2.0")
        assert result[0].value == 20.0
    finally:
        if original:
            PHASE_REGISTRY["highlight"] = original
