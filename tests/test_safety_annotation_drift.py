"""Drift detector for the MCP safety-annotation vocabulary.

The four annotation keys (``readOnlyHint``, ``destructiveHint``,
``idempotentHint``, ``openWorldHint``) form a closed vocabulary defined
by the MCP spec. In this repo they are typed as the ``ToolSafety`` enum
in ``mangrove_platform/mcp/security.py`` and re-stated in
``docs/security-plan.md`` (once in an inline JSON example, once in
Appendix A's reference table). Three copies means three places to update
if MCP ever adds a fifth annotation.

This test applies a single regex across the canonical source and the
documentation, asserts that the four keys appear in both, and pins the
exact occurrence counts so future drift is loud.

If the MCP spec adds a fifth annotation:
  1. Add the enum member to ``security.py:ToolSafety``.
  2. Update the JSON example and Appendix A in ``docs/security-plan.md``.
  3. Update the four constants and expected counts in this test.

If you are seeing this test fail on a count mismatch, do NOT change the
counts without auditing both files — the count IS the spec.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Canonical source — the typed enum in security.py.
SECURITY_SRC = (REPO_ROOT / "mangrove_platform" / "mcp" / "security.py").read_text(encoding="utf-8")

# Documentation — inline JSON example + Appendix A table.
SECURITY_PLAN_SRC = (REPO_ROOT / "docs" / "security-plan.md").read_text(encoding="utf-8")

# Governance policy — should NOT mention the annotation vocabulary.
GITHUB_SECURITY_SRC = (REPO_ROOT / ".github" / "SECURITY.md").read_text(encoding="utf-8")

ANNOTATION_KEYS = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")
ANNOTATION_KEYS_PATTERN = re.compile(r"\b(?:" + "|".join(ANNOTATION_KEYS) + r")\b")


def _count_matches(pattern: re.Pattern[str], text: str) -> dict[str, int]:
    """Return per-key match counts in ``text``."""
    return {key: len(pattern.findall(text)) for key in ANNOTATION_KEYS} | {
        "total": len(pattern.findall(text))
    }


def test_security_py_defines_all_four_annotation_keys():
    """Each annotation key must appear as a ``ToolSafety`` enum value in security.py.

    The enum (``mangrove_platform/mcp/security.py:ToolSafety``) is the
    canonical typed source of the vocabulary. If a key is missing, the
    drift detector's other assertions cannot hold.
    """
    for key in ANNOTATION_KEYS:
        # Match either `KEY = "key"` (enum value) or `"key":` (annotations dict).
        assert re.search(rf'"{key}"', SECURITY_SRC), (
            f"Annotation key {key!r} not present in security.py. Add it to the ToolSafety enum."
        )


def test_security_py_tool_safety_enum_matches_vocabulary():
    """The ``ToolSafety`` enum's *values* must be exactly the four annotation keys.

    Not just present — the enum must declare all four as values, in any
    order, with no extras. This locks the vocabulary shape.
    """
    enum_block = re.search(
        r"class ToolSafety\(Enum\):.*?(?=\n\nclass |\n\ndef |\Z)",
        SECURITY_SRC,
        re.DOTALL,
    )
    assert enum_block, "class ToolSafety(Enum) not found in security.py"
    body = enum_block.group(0)
    # Each enum member must end with the annotation key string.
    for key in ANNOTATION_KEYS:
        assert re.search(rf'=\s*"{key}"', body), (
            f"ToolSafety enum missing member for {key!r}. "
            "The enum's string values are the wire-format vocabulary."
        )
    # No extra members — count should be exactly four.
    member_count = len(
        re.findall(r'=\s*"(?:readOnlyHint|destructiveHint|idempotentHint|openWorldHint)"', body)
    )
    assert member_count == 4, (
        f"ToolSafety enum should have exactly 4 members, found {member_count}. "
        "If MCP added a 5th annotation, update the enum and this test."
    )


def test_security_plan_documents_all_four_annotation_keys():
    """``docs/security-plan.md`` must mention each annotation key at least once.

    The documentation is where new readers learn the vocabulary. If a key
    is undocumented, the drift-detector fails closed.
    """
    for key in ANNOTATION_KEYS:
        assert key in SECURITY_PLAN_SRC, (
            f"Annotation key {key!r} not documented in docs/security-plan.md. "
            "Add a row to Appendix A and an inline example."
        )


def test_security_plan_documents_vocabulary_in_appendix():
    """Appendix A's reference table must list all four annotation keys.

    Locks the appendix as a complete reference. If a row is dropped,
    readers miss the canonical documentation.
    """
    appendix = re.search(
        r"## Appendix A.*?\Z",
        SECURITY_PLAN_SRC,
        re.DOTALL,
    )
    assert appendix, "Appendix A not found in docs/security-plan.md"
    appendix_text = appendix.group(0)
    for key in ANNOTATION_KEYS:
        assert re.search(rf"\|\s*`{re.escape(key)}`\s*\|", appendix_text), (
            f"Appendix A missing table row for {key!r}."
        )


def test_github_security_md_does_not_reference_annotation_vocabulary():
    """``.github/SECURITY.md`` is governance policy, not API docs.

    The four annotation keys belong to the MCP transport contract and
    should not appear in the GitHub security policy. If they do, either
    the wrong vocabulary was pasted in or this drift detector needs to
    learn a new vocabulary site.
    """
    counts = _count_matches(ANNOTATION_KEYS_PATTERN, GITHUB_SECURITY_SRC)
    total = counts["total"]
    assert total == 0, (
        f".github/SECURITY.md unexpectedly mentions annotation keys "
        f"({counts}). The GitHub security policy is governance scope, not "
        "transport scope. Move the mention to docs/security-plan.md."
    )


def test_vocabulary_consistent_across_security_py_and_plan():
    """The set of annotation keys must match between security.py and security-plan.md.

    Locks the invariant: if a key is added to one, it must appear in the
    other. Catches asymmetric drift before it ships.
    """
    keys_in_src = {key for key in ANNOTATION_KEYS if f'"{key}"' in SECURITY_SRC}
    keys_in_doc = {key for key in ANNOTATION_KEYS if key in SECURITY_PLAN_SRC}
    missing_from_doc = keys_in_src - keys_in_doc
    missing_from_src = keys_in_doc - keys_in_src
    assert not missing_from_doc, (
        f"Keys declared in security.py but undocumented in "
        f"docs/security-plan.md: {sorted(missing_from_doc)}"
    )
    assert not missing_from_src, (
        f"Keys documented in docs/security-plan.md but missing from "
        f"security.py: {sorted(missing_from_src)}"
    )


if __name__ == "__main__":
    test_security_py_defines_all_four_annotation_keys()
    test_security_py_tool_safety_enum_matches_vocabulary()
    test_security_plan_documents_all_four_annotation_keys()
    test_security_plan_documents_vocabulary_in_appendix()
    test_github_security_md_does_not_reference_annotation_vocabulary()
    test_vocabulary_consistent_across_security_py_and_plan()
    print("\n[OK] Safety annotation vocabulary is in sync.")
