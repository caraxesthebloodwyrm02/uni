"""
Manual coverage tracer for the Apparat subsystem.

Uses sys.settrace() to track which lines of apparat source files are
executed during the test suite.  Does NOT depend on sqlite3 or coverage.py.

Usage:
    uv run python tests/apparat/trace_coverage.py
"""

import sys
from collections import defaultdict
from pathlib import Path

# Resolve the apparat source root
MANGROVE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(MANGROVE_ROOT.parent))
sys.path.insert(0, str(MANGROVE_ROOT / "mangrove_platform" / "apparat" / "src"))
APPARAT_ROOT = MANGROVE_ROOT / "mangrove_platform" / "apparat"

# Files to trace
TARGET_FILES = [
    APPARAT_ROOT / "apparat.py",
    APPARAT_ROOT / "horizontal_texture_processor.py",
    APPARAT_ROOT / "api.py",
    APPARAT_ROOT / "phase_handlers.py",
]

# Resolve to absolute strings for fast lookup
TARGET_PATHS = {str(f.resolve()) for f in TARGET_FILES if f.exists()}

# Track executed lines: {filepath: set(line_numbers)}
executed_lines: dict[str, set[int]] = defaultdict(set)


def _tracer(frame, event, arg):
    """Global trace function."""
    if event == "line":
        filename = frame.f_code.co_filename
        if filename in TARGET_PATHS:
            executed_lines[filename].add(frame.f_lineno)
    return _tracer


def count_source_lines(filepath: str) -> tuple[int, set[int]]:
    """Count executable source lines (non-blank, non-comment, non-docstring)."""
    source_lines = set()
    with open(filepath) as f:
        lines = f.readlines()
    in_docstring = False
    docstring_char = None
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if in_docstring:
            if stripped is not None and docstring_char in stripped:
                in_docstring = False
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_char = stripped[:3]
            if stripped.count(docstring_char) >= 2:
                continue
            in_docstring = True
            continue
        if not stripped or stripped.startswith("#"):
            continue
        source_lines.add(i)
    return len(source_lines), source_lines


def run_pytest_suite():
    """Run the actual pytest suite programmatically to trace real test execution."""
    import pytest

    # Run pytest on the apparat tests directory. Disable anyio as required by pyproject.toml.
    args = ["tests/apparat/", "-p", "no:anyio", "-v", "--tb=short"]
    return pytest.main(args)


def main():
    print("=" * 72)
    print("Apparat Coverage Tracer (no _sqlite3 required)")
    print("=" * 72)

    sys.settrace(_tracer)
    exit_code = run_pytest_suite()
    sys.settrace(None)

    print("\n" + "=" * 72)
    print("COVERAGE REPORT")
    print("=" * 72)
    total_source = 0
    total_hit = 0

    for fp in sorted(TARGET_PATHS):
        fname = Path(fp).name
        n_source, source_set = count_source_lines(fp)
        hit = executed_lines.get(fp, set()) & source_set
        n_hit = len(hit)
        missing = sorted(source_set - hit)
        pct = (n_hit / n_source * 100) if n_source else 0

        total_source += n_source
        total_hit += n_hit

        missing_ranges = []
        if missing:
            start = missing[0]
            end = start
            for line in missing[1:]:
                if line == end + 1:
                    end = line
                else:
                    missing_ranges.append(f"{start}-{end}" if start != end else str(start))
                    start = end = line
            missing_ranges.append(f"{start}-{end}" if start != end else str(start))

        missing_str = ", ".join(missing_ranges) if missing_ranges else ""
        print(f"\n{fname:<45s} {n_hit:>4d}/{n_source:<4d}  {pct:5.1f}%")
        if missing_str:
            print(f"  Missing: {missing_str}")

    total_pct = (total_hit / total_source * 100) if total_source else 0
    print(f"\n{'TOTAL':<45s} {total_hit:>4d}/{total_source:<4d}  {total_pct:5.1f}%")
    print("=" * 72)
    print(f"\nPytest exited with code: {exit_code}")


if __name__ == "__main__":
    main()
