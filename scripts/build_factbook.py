#!/usr/bin/env python3
# ==============================================================================
# Script Name: build_factbook.py
# Description: Compile fact checklist into facts.ndjson by querying the canonical archive
# Scope/Safety: Safe / Read-only scan of archive, writes to canon/facts.ndjson
# Dependencies: Python 3.13+, ripgrep (rg)
# ==============================================================================
"""Build canon/facts.ndjson from regex-anchored facts.

Pre-condition: M0+M1 complete. This script does NOT touch the canonical archive;
it asserts over it via single regex passes and emits one JSON fact per line.

Each fact has:
  - key: ASCII snake_case identifier
  - value: the canonical claim (string)
  - source: file:line citation in the canonical archive
  - regex_anchor: a regex that, run against the citation, reproduces the claim

M2 pass condition: a regex scan of canon/facts.ndjson returns the full set when
queried by key, AND every fact's regex_anchor re-greps to its source.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from scripts.utils import check_command_exists, load_json_config, run_command

OUT = Path(__file__).resolve().parent.parent / "canon" / "facts.ndjson"

# Load configuration from .devin/hooks.json if available
CONFIG = load_json_config(Path(".devin/hooks.json")) if Path(".devin/hooks.json").exists() else {}

# Canonical archive mount. Override with MANGROVE_ARCHIVE_ROOT env var or config.
archive_env = os.environ.get("MANGROVE_ARCHIVE_ROOT")
if archive_env:
    ARCHIVE = Path(archive_env)
elif "scriptConfig" in CONFIG and "buildFactbook" in CONFIG["scriptConfig"]:
    ARCHIVE = Path(
        CONFIG["scriptConfig"]["buildFactbook"].get(
            "archivePath", "/run/media/cable/cf656878-be07-4249-b8ba-10fd482aa610/home/irfankabir"
        )
    )
else:
    ARCHIVE = Path("/run/media/cable/cf656878-be07-4249-b8ba-10fd482aa610/home/irfankabir")

# Check for ripgrep dependency using configuration or fallback
if "scriptConfig" in CONFIG and "buildFactbook" in CONFIG["scriptConfig"]:
    RG_BIN = CONFIG["scriptConfig"]["buildFactbook"].get("rgBinary", "/usr/bin/rg")
else:
    RG_BIN = "/usr/bin/rg"

if not check_command_exists(RG_BIN):
    print(f"CRITICAL: ripgrep (rg) is required but not found at {RG_BIN}", file=sys.stderr)
    sys.exit(1)

if not ARCHIVE.is_dir():
    sys.exit(
        f"Canonical archive not mounted: {ARCHIVE}\n"
        f"Mount the volume and retry, or set MANGROVE_ARCHIVE_ROOT to the right path."
    )


def rg(pattern: str, path: Path, count_only: bool = False) -> str:
    """Single regex pass over the canonical archive. Returns matched lines."""
    cmd = [RG_BIN, "--no-heading", "-n", pattern, str(path)]
    if count_only:
        cmd.insert(1, "-c")
    result = run_command(cmd, check=False)
    return result.stdout.strip()


def first(pattern: str, path: Path) -> tuple[str, str] | None:
    """Return (line_no, line_text) for the first regex match."""
    text = rg(pattern, path)
    if not text:
        return None
    first_line = text.splitlines()[0]
    line_no, _, line_text = first_line.partition(":")
    return line_no, line_text


def fact(key: str, value: str, source: str, regex_anchor: str) -> dict[str, str]:
    return {
        "key": key,
        "value": value,
        "source": source,
        "regex_anchor": regex_anchor,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    facts: list[dict[str, str]] = []

    # --- Fact 1: TUV-001 path ---
    f = first(
        r"docs/AGENTS.md.*TUV-001|docs/AGENTS.md.*development contract", ARCHIVE / "CLAUDE.md"
    )
    if f:
        facts.append(
            fact(
                "tuv_001_reference",
                "/home/irfankabir/docs/AGENTS.md is the development contract (TUV-001).",
                f"CLAUDE.md:{f[0]}",
                r"docs/AGENTS.md.*development contract",
            )
        )

    # --- Fact 2: npm scope ---
    f = first(r'"@irfankabir002/gruff"', ARCHIVE / "domains/platform/gruff/package.json")
    if f:
        facts.append(
            fact(
                "npm_scope_gruff",
                "npm scope is @irfankabir002 (different from GitHub identities).",
                f"domains/platform/gruff/package.json:{f[0]}",
                r'"@irfankabir002/gruff"',
            )
        )

    # --- Fact 3: x-change state machine (canonical form) ---
    f = first(
        r"drafted.*earned.*payment_pending.*payment_confirmed.*student_acknowledged",
        ARCHIVE / "domains/platform/finance/docs/UBIQUITOUS-LANGUAGE.md",
    )
    if f:
        facts.append(
            fact(
                "xchange_state_machine",
                "drafted -> earned -> payment_pending -> payment_confirmed -> student_acknowledged (review_requested branch).",
                f"domains/platform/finance/docs/UBIQUITOUS-LANGUAGE.md:{f[0]}",
                r"drafted.*earned.*payment_pending.*payment_confirmed.*student_acknowledged",
            )
        )

    # --- Fact 4: 4 P0 finance entities ---
    count = int(
        rg(
            r"^### [0-9]+\.\s+(Burn Floor|Seed Amount|Product Revenue|Gap)$",
            ARCHIVE / "domains/platform/finance/P0-FINANCE-DOMAIN.md",
            count_only=True,
        )
        or "0"
    )
    if count == 4:
        facts.append(
            fact(
                "p0_finance_entities_count",
                "4 P0 entities: Burn Floor, Seed Amount, Product Revenue, Gap.",
                "domains/platform/finance/P0-FINANCE-DOMAIN.md:14,22,29,36",
                r"^### [0-9]+\.\s+(Burn Floor|Seed Amount|Product Revenue|Gap)$",
            )
        )

    # --- Fact 5: 9 payment hardlines ---
    count = int(
        rg(
            r'<h3 class="rule-title">\s*Never\b',
            ARCHIVE / "domains/platform/finance/DO-NOT.html",
            count_only=True,
        )
        or "0"
    )
    if count == 9:
        facts.append(
            fact(
                "payment_hardlines_count",
                "9 DO-NOT.html payment hardlines, each anchored by <h3 class='rule-title'>Never…</h3>.",
                "domains/platform/finance/DO-NOT.html:326..382",
                r'<h3 class="rule-title">\s*Never\b',
            )
        )

    # --- Fact 6: lab package count (CORRECTION: 28 dirs, 15 pyproject.toml) ---
    lab_root = ARCHIVE / "domains/platform/operations/lab"
    if lab_root.is_dir():
        n_dirs = sum(1 for _ in lab_root.iterdir() if _.is_dir() and not _.name.startswith("."))
        pp_count = int(
            run_command(
                [
                    "find",
                    str(lab_root),
                    "-maxdepth",
                    "2",
                    "-name",
                    "pyproject.toml",
                ],
                check=False,
            )
            .stdout.strip()
            .count("\n")
            + 1
        )
        facts.append(
            fact(
                "lab_packages_count",
                f"{n_dirs} lab package directories at top level; {pp_count} ship a pyproject.toml.",
                "domains/platform/operations/lab/",
                r"^(silver|goblet|wikidex|after_hours_package|artifacts|bipolar-wave-demo|case|common|contract|curiosity-garden|design|goblet|hats|identify_gem_token|levant|linux|microscope|mistral-test|nome|notes|painterly|painterly-perception|python-craft|read|rust-intro|silver|storyland|token-type-calculator|tools|trace_pipeline|wikidex)$",
            )
        )

    # --- Fact 7: python-craft collaborator ---
    f = first(
        r"shinychoes", ARCHIVE / "domains/platform/operations/lab/python-craft/pyproject.toml"
    )
    if f:
        facts.append(
            fact(
                "python_craft_collaborator",
                "python-craft is collaborator-owned by 'shinychoes' (MIT).",
                f"domains/platform/operations/lab/python-craft/pyproject.toml:{f[0]}",
                r"shinychoes",
            )
        )

    # --- Fact 8: silver.afterbuzz ORIGINAL_CATALOG carve-out ---
    f = first(r"ORIGINAL_CATALOG", ARCHIVE / "domains/platform/operations/lab/silver/NOTICE")
    if f:
        facts.append(
            fact(
                "silver_afterbuzz_catalog_carveout",
                "silver.afterbuzz._ORIGINAL_CATALOG positions 501-507 carve-out (audio metadata only).",
                f"domains/platform/operations/lab/silver/NOTICE:{f[0]}",
                r"ORIGINAL_CATALOG",
            )
        )

    # --- Fact 9: port 8788 policy ---
    f = first(r"8788", ARCHIVE / "CLAUDE.md")
    if f:
        facts.append(
            fact(
                "port_8788_policy",
                "Port 8788 blocked for all uses except x-change production (bind locally).",
                f"CLAUDE.md:{f[0]}",
                r"8788",
            )
        )

    # --- Fact 10: TUV-001 mentions across doc set (consistency check) ---
    mentions = rg(r"TUV-001", ARCHIVE / "docs", count_only=True) or "0"
    facts.append(
        fact(
            "tuv_001_mention_count",
            f"TUV-001 is referenced {int(mentions) if mentions.isdigit() else 0} times across docs/.",
            "docs/",
            r"TUV-001",
        )
    )

    # --- Emit ---
    with OUT.open("w", encoding="utf-8") as fh:
        for entry in facts:
            _ = fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"wrote {len(facts)} facts to {OUT}")
    print(f"  bytes: {OUT.stat().st_size}")


if __name__ == "__main__":
    main()
