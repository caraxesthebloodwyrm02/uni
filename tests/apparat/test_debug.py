from mangrove_platform.apparat.api import GridCell
from mangrove_platform.apparat.debug import apa_dbg, disable, enable, is_enabled
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor


def test_debug_enable_disable():
    """Verify enabling and disabling the debug surface."""
    disable()
    assert not is_enabled()
    assert not apa_dbg.is_enabled()

    enable()
    assert is_enabled()
    assert apa_dbg.is_enabled()
    disable()


def test_debug_record_flow():
    """Verify recording events and marking status."""
    enable()
    processor = HorizontalTextureProcessor(4, 4)
    processor.ipo.input_data = [GridCell(0, 0, 0.5, "empty")]

    # Record phase start
    apa_dbg.record(processor, "scale:2.0", {"factor": 2.0}, status="started")
    hist = apa_dbg.history()
    assert len(hist) == 1
    assert hist[0]["phase"] == "scale:2.0"
    assert hist[0]["status"] == "started"
    assert hist[0]["cell_count"] == 1

    # Mark success
    apa_dbg.mark_ok("scale:2.0", {"factor": 2.0})
    hist = apa_dbg.history()
    assert hist[0]["status"] == "ok"

    # Record phase start again and mark error
    apa_dbg.record(processor, "quantize", {}, status="started")
    apa_dbg.mark_error("quantize", "Some error occurred")

    hist = apa_dbg.history()
    assert len(hist) == 2
    assert hist[1]["status"] == "error"
    assert hist[1]["error"] == "Some error occurred"

    err = apa_dbg.last_error()
    assert err is not None
    assert err["phase"] == "quantize"
    assert err["error"] == "Some error occurred"

    disable()


def test_debug_introspection_failure_absorption():
    """Verify that introspection failures do not raise exceptions but populate error fields."""
    enable()

    # A mock processor that raises an exception when accessing 'ipo'
    class CorruptProcessor:
        @property
        def ipo(self):
            raise ValueError("Introspection crash test")

    proc = CorruptProcessor()

    # Recording should not raise an exception
    apa_dbg.record(proc, "test_phase", {})

    hist = apa_dbg.history()
    assert len(hist) == 1
    assert hist[0]["status"] == "error"
    assert "introspection_failed" in hist[0]["error"]

    disable()


def test_debug_dump_state():
    """Verify dump_state output formatting."""
    processor = HorizontalTextureProcessor(4, 4)
    processor.ipo.input_data = [GridCell(0, 0, 1.0, "empty")]
    processor.ipo.processed_data = [GridCell(0, 0, 1.0, "empty")]
    processor.ipo.output_data = [GridCell(0, 0, 1.0, "empty")]
    processor.ipo.render_snapshot = [[1.0]]

    state = apa_dbg.dump_state(processor)
    assert state["resolution"] == [4, 4]
    assert state["input_count"] == 1
    assert state["processed_count"] == 1
    assert state["output_count"] == 1
    assert state["render_rows"] == 1
    assert "current_phase" in state


if __name__ == "__main__":
    test_debug_enable_disable()
    test_debug_record_flow()
    test_debug_introspection_failure_absorption()
    test_debug_dump_state()
    print("PASS: test_debug endpoints")
