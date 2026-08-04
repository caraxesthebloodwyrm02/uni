#!/usr/bin/env python3
"""
validate_workspace.py
Consolidates workspace structure, large files, secrets, and 3PAA-SHADOW
containment checks previously handled by multiple bash scripts.
"""

import os
import re
import sys
from pathlib import Path

MAX_SIZE_KB = 500
FORBIDDEN_DOMAINS = re.compile(r"factory\.ai|cursor\.com|cursor\.sh|workos\.com")
FORBIDDEN_TOKENS = re.compile(r"WorkOS|Factory")
SECRET_PATTERNS = re.compile(
    r'(?i)(password\s*=\s*[\'"]|api[_-]?key\s*=\s*[\'"]|secret\s*=\s*[\'"]|'
    r'token\s*=\s*[\'"]|credential\s*=\s*[\'"]|aws[_-]?access[_-]?key\s*=|'
    r"private[_-]?key\s*=|bearer\s+[A-Za-z0-9_\-\.]+)"
)

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "htmlcov",
    ".mypy_cache",
    ".opencode",
    ".pytest_cache",
    ".devin",
    "__pycache__",
}
# Additional file to ignore per original bash lib
EXCLUDE_FILES = {"mangrove_platform/apparat/phase_handlers.py", "scripts/validate_workspace.py"}
PATTERN_CHECK_SKIP_PREFIXES = ("tests/",)


def report_error(msg: str):
    print(f"\033[0;31m[ERROR] {msg}\033[0m", file=sys.stderr)


def report_warning(msg: str):
    print(f"\033[1;33m[WARN] {msg}\033[0m")


def report_success(msg: str):
    print(f"\033[0;32m[OK] {msg}\033[0m")


def iter_workspace_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Mutate dirnames to skip excluded dirs
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            yield Path(dirpath) / f


def check_workspace_structure(root: Path) -> tuple[int, int]:
    errors = 0
    warnings = 0

    # Check for empty directories

    empty_dirs = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if not dirnames and not filenames:
            empty_dirs.append(dirpath)

    if empty_dirs:
        # We don't error on empty dirs directly in root usually, but report them.
        for ed in empty_dirs:
            # Replicate the audit_workspace.sh behavior (informational)
            print(f"  EMPTY: {Path(ed).relative_to(root)}")

    # Check for python cache
    pycache_dirs = list(root.rglob("__pycache__"))
    # filter out venv
    pycache_dirs = [d for d in pycache_dirs if ".venv" not in d.parts and "venv" not in d.parts]
    if pycache_dirs:
        report_warning(f"Python cache directories found in project: {len(pycache_dirs)} found.")
        warnings += 1
    else:
        report_success("No Python cache in project directories")

    # Check for transcript files
    transcript_files = list(root.glob("*.txt"))
    transcript_files = [f for f in transcript_files if f.name not in ("LICENSE", "NOTICE")]
    if transcript_files:
        report_error(f"Transcript files found: {[f.name for f in transcript_files]}")
        errors += 1
    else:
        report_success("No transcript files found")

    return errors, warnings


def check_files(root: Path) -> tuple[int, int]:
    errors = 0
    warnings = 0

    large_files = []
    forbidden_domain_files = []
    forbidden_token_files = []
    secret_files = []

    for filepath in iter_workspace_files(root):
        try:
            rel_path = filepath.relative_to(root).as_posix()
        except ValueError:  # noqa: S112
            continue

        if rel_path in EXCLUDE_FILES:
            continue

        if not filepath.is_file():
            continue

        # Size check
        size_kb = filepath.stat().st_size / 1024
        if size_kb > MAX_SIZE_KB:
            large_files.append((rel_path, size_kb))

        # Pattern checks
        if rel_path.startswith(PATTERN_CHECK_SKIP_PREFIXES):
            continue
        if filepath.suffix in (".py", ".toml", ".yaml", ".yml", ".json"):
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                if FORBIDDEN_DOMAINS.search(content):
                    forbidden_domain_files.append(rel_path)
                if FORBIDDEN_TOKENS.search(content):
                    forbidden_token_files.append(rel_path)
                if SECRET_PATTERNS.search(content):
                    secret_files.append(rel_path)
            except Exception:  # noqa: S110
                pass
    if large_files:
        report_error(f"Large files detected (>{MAX_SIZE_KB}KB):")
        for f, s in large_files:
            print(f"  {f} ({s:.1f} KB)")
        errors += 1
    else:
        report_success("No large files found")

    if forbidden_domain_files:
        report_error("Forbidden domains detected (3PAA-SHADOW containment)")
        for f in forbidden_domain_files:
            print(f"  {f}")
        errors += 1
    else:
        report_success("No forbidden domains found")

    if forbidden_token_files:
        report_error("Forbidden tokens detected (3PAA-SHADOW containment)")
        for f in forbidden_token_files:
            print(f"  {f}")
        errors += 1
    else:
        report_success("No forbidden tokens found")

    if secret_files:
        report_warning(f"Potential secrets detected in: {', '.join(secret_files)}")
        warnings += 1
    else:
        report_success("No potential secrets found")

    return errors, warnings


def main():
    print("\033[0;34mWorkspace Validation\033[0m")
    print("==========================")
    root = Path(__file__).resolve().parent.parent
    e1, w1 = check_workspace_structure(root)
    e2, w2 = check_files(root)
    errors = e1 + e2
    warnings = w1 + w2
    print("\n==========================")
    print("\033[0;34mValidation Summary\033[0m")
    print("==========================")
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    if errors == 0 and warnings == 0:
        print("\033[0;32mSuccess checks: All checks passed\033[0m")
        sys.exit(0)
    else:
        print("\033[0;31mSuccess checks: Some checks failed\033[0m")
        if errors > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
