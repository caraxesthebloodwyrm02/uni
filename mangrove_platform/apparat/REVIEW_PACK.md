# M5: Review Pack
_Generated: 2026-08-01T06:46:56_

## Phase 1 — Targeted Reads & Workspace Synthesis

### Sub-projects surfaced
- **galvastron**: Go-based registry CLI for 3D project mapping
- **mangrove**: Polyglot ecosystem for finance/intelligence/platform
- **playground**: Sandboxed Python laboratory for rapid prototyping

### Authority documents
- `series_CLAUDE.md`: `/home/cable/series/mangrove/CLAUDE.md`
- `mangrove_CLAUDE.md`: `/home/cable/series/mangrove/mangrove/CLAUDE.md`
- `playground_AGENTS.md`: `/home/cable/series/mangrove/playground/AGENTS.md`

## Phase 2 — Tripwire Tests & Dispatcher

### Tripwire configuration
- Test file: `/home/cable/series/mangrove/tests/apparat/test_validate_acceleration.py`
- Checks executed:
  - `baseline_normalization`
  - `cruise_engagement`
  - `slice_contract`
  - `security_and_guardrails`
- Exit-code table:
  - `all_pass`: exit **0**
  - `unhandled_exception`: exit **1**
  - `baseline_violation`: exit **2**
  - `cruise_failure`: exit **3**
  - `slice_violation`: exit **4**
  - `security_failure`: exit **5**

### Regex-driven dispatcher
- File: `/home/cable/series/mangrove/platform/apparat/horizontal_texture_processor.py`
- Regex-driven dispatcher supporting 'phase:arg1,arg2' syntax
- Phases supported:
  - `normalize`
  - `scale`
  - `clamp`
  - `filter`
  - `invert`
  - `initiate`
  - `quantize`
  - `combine`
  - `render`
  - `complete`

### Materialized components
- `platform/apparat/apparat.py`
- `platform/apparat/phase_handlers.py`
- `platform/apparat/horizontal_texture_processor.py`
- `platform/apparat/src/golding/validate.py`
- `platform/apparat/src/golding/code/validate.py`

## Operating notes

- All Python execution via `uv run`; never bare `python` or `pip`.
- Live tree is a stub; canonical archive on the volume (UUID `cf656878-...`).
- To rerun the tripwire: `cd mangrove && uv run pytest tests/apparat/test_validate_acceleration.py`
