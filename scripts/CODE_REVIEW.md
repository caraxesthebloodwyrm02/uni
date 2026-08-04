# Code Review: scripts/

**Date:** 2026-08-03
**Scope:** 18 scripts + `__init__.py` + `ssl_workarounds.md` in `/home/cable/series/mangrove/scripts/` (1,673 lines total)
**Reviewer dimensions:** correctness, security, robustness, performance, simplification, test coverage, error handling, documentation

## Status (2026-08-04)

Findings resolved or retracted during the 2026-08-04 closing-session pass:

| ID | Severity | Status | Notes |
|---|---|---|---|
| F1 | CRITICAL | **Retracted** | `validate-lib.sh` is load-bearing — sourced on line 8 of `check-secrets.sh`, `check-large-files.sh`, `check-forbidden-patterns.sh`, and `validate-workspace.sh` (the last of which uses 7+ exports). "Zero callers" was incorrect. |
| F2 | CRITICAL | **Retracted** | `attribution_oscillator.py` is a plain SHA256 chain writer. There is no sine-wave "squash" and no hardcoded `"VERIFIED"` string. The docstring explicitly states "no verification claim is made." Always exits 0 per docstring. |
| F3 | CRITICAL | **Resolved** | `scripts/browser_global_assistance_audit.py` deleted from the working tree (status `D` in `git status`). |
| F4 | CRITICAL | **Resolved** | `scripts/branch-audit.sh` deleted; `prune-stale-branches.sh` is the live version. CSV at `.compliance-hand-off/branch-audit.csv` is now produced only by the live script. |
| F5 | HIGH | Open | `guardrail_heatmap.py` literal-string coupling remains. Low priority. |
| F6 | HIGH | **Partially resolved** | `build_factbook.py` already had a module-level mount-check guard (`if not ARCHIVE.is_dir(): sys.exit(...)` at line 35). Added defensive `is_dir()` guard around Fact 6's `lab/` iteration (lines 154-184) so a missing `lab/` subpath degrades to "no fact" instead of `FileNotFoundError`. |
| F7 | MEDIUM | **Resolved** | `check-secrets.sh:29-32` and `check-large-files.sh:17-20` already had explicit "no staged files" branches. Added the same guard to `check-forbidden-patterns.sh` git-context branch; also added explicit "no unstaged files" branch. |
| F8 | MEDIUM | **Resolved** | `MAX_SIZE_MB=5` no longer exists in any file — removed by prior work. |
| F9 | MEDIUM | **Partially resolved** | `validate-workspace.sh` final-summary block now uses `report_error` / `report_warning` / `report_success` instead of inline `${RED}/${YELLOW}/${GREEN}` echoes. Header banners (BLUE) remain for visual section structure. |
| F10 | MEDIUM | Open | The `find` expression with the 11-exclude path list is still repeated in `check-forbidden-patterns.sh:60-75` and `validate-workspace.sh:65-78, 75-78, 88-91`. Centralizing this would require a small helper in `validate-lib.sh`; deferred. |
| F11 | LOW | Open | `profile_apparat.py` lacks top-level import error handling. |
| F12–F18 | LOW/TESTING | Open | Lower-priority cleanup; not in this session's scope. |

---

---

## Findings (most-severe first)

### F1 — `validate-lib.sh` is dead code (CRITICAL)

**File:** `scripts/validate-lib.sh:1-77` (76 lines)

The shared validation library exports `RED`/`GREEN`/`YELLOW`/`BLUE`/`NC` color variables, `MAX_SIZE_KB`/`FORBIDDEN_DOMAINS`/`FORBIDDEN_TOKENS`/`EXCLUDE_FILES` config defaults, `errors`/`warnings`/`violations_found` counters, and four functions: `report_error`, `report_warning`, `report_success`, `init_validation`, `in_git_repo`. **Zero callers** — no script sources it, no workflow invokes it, no test references it. The function `in_git_repo` (line 74) is defined but never used even within `validate-lib.sh` itself.

This is the central piece of dead code: it was added in commit `abcbd24` ("centralize validation scripts") with the intent of refactoring the check scripts, but the refactor never happened. The 4 check scripts (`check-forbidden-patterns.sh`, `check-secrets.sh`, `check-large-files.sh`, `validate-workspace.sh`) all duplicate its color variables, counter names, and config-loading logic inline.

**Risk:** Future agents see `validate-lib.sh` and assume it is the source of truth. Modifying it does nothing. The "shared" abstraction is a lie.

**Recommendation:** Either (a) refactor the 4 check scripts to `source "${SCRIPT_DIR}/validate-lib.sh"` and call `init_validation "${CONFIG_FILE:-.devin/hooks.json}"`, or (b) delete `validate-lib.sh` and inline-document why the duplication exists.

---

### F2 — `attribution_oscillator.py` is decorative audit theater (CRITICAL)

**File:** `scripts/attribution_oscillator.py:1-116` (116 lines)

The script computes a SHA256 of `{runtime_ts, env_user, env_host, env_py, binary_shas, prev_head, new_head}`, then runs the digest through a sine-wave "squash" (`calculate_sine_squash`, lines 37-57) that maps each byte to a phase angle and sums `|sin(phase)|`. The output is a fixed-precision float `0.0000–1.0000`. The script hardcodes a `constraint_stmt = "INTELLIGENCE_AUTH_VERIFIED"` regardless of the math result.

**Issues:**
1. The sine-wave transformation has no statistical meaning; it is mathematical decoration.
2. The "VERIFIED" status string is hardcoded and never derived from the math.
3. The output is appended to `.compliance-hand-off/.audit.log` but **no enforcement gate reads the log entries** — `.devin/hooks.json` pre-push checks are `run-tests, workspace-audit`; pre-commit checks are `check-forbidden-patterns, ruff-lint, ruff-format, check-secrets, check-large-files`. CI workflows (`.github/workflows/ci.yml`, `prune-stale-branches.yml`) do not invoke this script.
4. The script never returns a non-zero exit code based on the math; it always exits 0. So even if the math detected something, the caller would not know.

**Risk:** Operators who read the log may believe the workspace has been "verified" by this script when in fact only a SHA256 has been computed. Misleading audit trail.

**Recommendation:** Remove. If the SHA256 chain is genuinely needed for compliance, write a 20-line `audit_chain.py` that appends the digest + envelope and exit 0; drop the sine math.

---

### F3 — `browser_global_assistance_audit.py` is a tautology (CRITICAL)

**File:** `scripts/browser_global_assistance_audit.py:25-46`

The script launches headless Chrome against a `data:` URL:
```
data:text/html,<html><body><div id='global-assistance'>GLOBAL_ASSISTANCE_ACTIVE</div></body></html>
```
Then greps the dumped DOM for the literal string `GLOBAL_ASSISTANCE_ACTIVE`. **The string is hardcoded in the URL being loaded.** The check therefore always succeeds (subject to Chrome being installed and the 15-second timeout).

**Issues:**
1. No real endpoint is contacted. The "endpoint transparency" claim is false.
2. No version check, no SSL verification, no actual service is audited.
3. The output JSON `browser-assistance-audit.json` claims `global_assistance_active: true` regardless of what any real service is doing.

**Risk:** If a CI workflow ever adopts this, it gives a green light for any state of the world.

**Recommendation:** Remove. If real browser-based audit is needed later, write a Playwright-based test against a real URL with assertions about the actual response.

---

### F4 — `branch-audit.sh` writes stub data and is dead (CRITICAL)

**File:** `scripts/branch-audit.sh:39-79` (function `get_pr_metadata`)

The function `get_pr_metadata` returns hardcoded data for "PR #12" (feat: Add new validation framework, 2024-07-15) and "PR #13" (fix: Resolve import errors, 2024-07-20). All other PR numbers return 1970-01-01 placeholder data. The function never calls the GitHub API.

**Issues:**
1. The output `.compliance-hand-off/branch-audit.csv` is the same file that `prune-stale-branches.sh` writes (and that `.github/workflows/prune-stale-branches.yml` artifact-uploads). Two scripts writing to one file is a race condition.
2. The stub PR data is dated 2024-07, which is older than the 2026 commits in the repo — anyone inspecting the CSV will see obviously fake data.
3. The script is **not called by any CI workflow** (verified by `grep` of `.github/workflows/*.yml`).
4. The diff-stat parsing on lines 100-103 is fragile: `git diff --stat ... | head -1 | awk '{print $1+$2+$3+$4+$5+$6}'` adds columns that are actually filenames and file-change tuples, not numeric counts. A repo with one file changed will produce `1+0+0+0+0+0 = 1`, but a repo with 12 files shows `12+0+0+0+0+0 = 12` only if the first line has 12 column entries; in practice `git diff --stat` produces lines like `12 files changed, 45 insertions(+), 12 deletions(-)`, so the head -1 awk count is incorrect.

**Recommendation:** Remove. `prune-stale-branches.sh` is the live version.

---

### F5 — `guardrail_heatmap.py` heuristic checks imports that are required (HIGH)

**File:** `scripts/guardrail_heatmap.py:47-67`

The "Namespace Poisoning" scope checks `mangrove_platform/mcp/apparat_server.py` for the string `from mcp import`. If found, severity = 2 (EXPOSED). But the `apparat_server.py` module **must** import from `mcp` to use FastMCP — this is a required dependency, not a vulnerability.

Similarly, the "I/O Data Overwrite" check at line 60 looks for the exact substring:
```python
if 'with open(metrics_file, "w") as f:\n        json.dump(metrics' in text:
```
This is a literal string match for a specific implementation pattern. Any refactor of the test file (extra spaces, different variable name) would silently flip the severity to SAFE without the underlying behavior changing.

**Issues:**
1. The "recursive check" reads exactly 1-2 files; the name "recursive" is misleading.
2. The severity rules are coupled to literal source strings, not semantic properties.
3. The output `.compliance-hand-off/guardrail-heatmap.json` is generated but never read by any enforcement gate.

**Risk:** False positives/negatives based on whitespace. Operators may believe the heatmap represents real vulnerability analysis.

**Recommendation:** Remove. If a real lint of `apparat_server.py` is wanted, use `ruff check mangrove_platform/mcp/apparat_server.py` with a bandit rule.

---

### F6 — `build_factbook.py` reads from a path that does not exist (HIGH)

**File:** `scripts/build_factbook.py:23`

```python
ARCHIVE = Path("/run/media/cable/cf656878-be07-4249-b8ba-10fd482aa610/home/irfankabir")
```

This path is a specific UUID of a volume that is **not currently mounted on this host** (verified — `mount | grep -i irfan` returns empty; `/mnt/` is empty; `/run/media/cable/` is unverified but the volume UUID matches the `cf656878-...` referenced in the committed `TERMS_OF_ENGAGEMENT.md`).

**Issues:**
1. The script will run, attempt 10 regex scans, fail silently (the `rg` wrapper returns empty strings for missing paths), and write an empty/minimal `canon/facts.ndjson` overwriting any existing facts.
2. There is no pre-check for `ARCHIVE.exists()`. The `first()` helper returns `None` for missing files, and the surrounding `if f:` guards skip the fact, but **Fact 6 (`lab_packages_count`, line 141-170) has no guard** — it iterates `ARCHIVE / "domains/platform/operations/lab"` which will raise `FileNotFoundError`.
3. Lines 147-162 use `subprocess.run(["find", ...])` with `text=True` and then count newlines + 1, which is off-by-one (a single result has 0 newlines, so the count would be 1 + 0 = 1 — coincidentally correct; but the implementation is fragile).
4. The committed `canon/facts.ndjson` has 9 facts, but the script generates up to 10 (it includes `port_8788_policy` which isn't in the committed set). Running this script would *change* the committed canon.

**Recommendation:** Add a guard at the top: `if not ARCHIVE.is_dir(): sys.exit(f"Archive not mounted: {ARCHIVE}")`. Document the prerequisite in the docstring and the script's first line.

---

### F7 — `check-secrets.sh` exits 0 when git has no staged changes (MEDIUM)

**File:** `scripts/check-secrets.sh:27-37`

The `git diff --cached --name-only --diff-filter=ACM` produces empty output when nothing is staged. The `while read file` loop never executes, and `suspicious_files` is empty. The script prints `✓ No potential secrets found` and exits 0.

This is a **silent pass for the no-op case**. Running the pre-commit hook on a directory where nothing is staged will report success even though no check was performed. Operators may believe the workspace is secret-free.

The same issue applies to `check-large-files.sh` (line 18) and `check-forbidden-patterns.sh` (line 28) in git-context mode.

**Recommendation:** Add a check: if `git diff --cached --name-only` is empty, exit 0 with a clear message ("No staged files; skipping check"), or distinguish the empty-staged case from a real pass.

---

### F8 — `check-large-files.sh` checks KB but allows MB-cap-only (MEDIUM)

**File:** `scripts/check-large-files.sh:7-8`

```bash
MAX_SIZE_KB=500  # 500KB limit for code files
MAX_SIZE_MB=5    # 5MB limit for any file
```

`MAX_SIZE_MB` is declared but **never referenced in the script body**. Only `MAX_SIZE_KB` is used (line 21: `if [ "$size" -gt "$MAX_SIZE_KB" ]`). The 5MB cap is dead config.

**Risk:** Operators reading the script may believe a 5MB tier exists. Documentation in `.devin/hooks.json::maxFileSizeKB: 500` matches `MAX_SIZE_KB` but not `MAX_SIZE_MB`.

**Recommendation:** Either implement the two-tier cap (e.g., 500KB warn, 5MB error) or remove the `MAX_SIZE_MB=5` line.

---

### F9 — `validate-workspace.sh` has duplicate jq-defaulting logic (MEDIUM)

**File:** `scripts/validate-workspace.sh:18-29` vs `scripts/validate-lib.sh:50-60`

Both files contain nearly identical logic for loading `.devin/hooks.json` and falling back to defaults. `validate-workspace.sh` doesn't source `validate-lib.sh`; it duplicates the inline jq invocations. This is the canonical "shared library is unused" symptom from F1.

**Recommendation:** Fold into the F1 fix: source `validate-lib.sh` from both.

---

### F10 — `check-forbidden-patterns.sh` has duplicate paths in find expressions (MEDIUM)

**File:** `scripts/check-forbidden-patterns.sh:56-72` (and 100-116 in `validate-workspace.sh`)

The `find` expression is repeated **four times** in two scripts:
```bash
find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
    ! -path "./.venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
    ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" \
    -exec grep -lE "$PATTERN" {} \; 2>/dev/null || true
```

The exclude `*/mangrove_platform/apparat/phase_handlers.py` exists because that file legitimately contains references to `WorkOS`/`Factory` in its non-secret context — the script bakes the exception into the path. But the path is also hardcoded in `EXCLUDE_FILES="mangrove_platform/apparat/phase_handlers.py|.devin/"` (line 20) for the git-context branch, and again in `validate-workspace.sh` and `.pre-commit-config.yaml`.

**Recommendation:** Promote the exclude list to a single variable in `validate-lib.sh` and use it everywhere.

---

### F11 — `profile_apparat.py` has no error handling around import (LOW)

**File:** `scripts/profile_apparat.py:14-15`

The imports of `apparat.horizontal_texture_processor` and `apparat_logic` are at module top-level, not guarded by try/except. If the Apparat subsystem fails to load (e.g., missing dependency, syntax error in `phase_handlers.py`), the script crashes with a Python traceback. The `warmup_apparat.py` script handles this with a try/except and a clean error message (line 21-27).

**Recommendation:** Add the same try/except pattern as `warmup_apparat.py` for consistency.

---

### F12 — `prune-stale-branches.sh` writes CSV without quoting (LOW)

**File:** `scripts/prune-stale-branches.sh:49`

```bash
echo "${branch},${date_iso},${sha},${merged},${rec}" >> "$OUT_FILE"
```

`$date_iso` comes from `git show -s --format=%ci "$sha"` which is `YYYY-MM-DD HH:MM:SS +ZZZZ`. No commas, but the branch name **could** contain commas (e.g., `feature/foo,bar`). The `rec` field is one of `keep` / `delete (merged)` / `stale (>=90d)` — no commas. The risk is branch names with commas breaking the CSV.

**Recommendation:** Wrap each field in double quotes, or use a CSV writer. Same fix for `branch-audit.sh` if it's not removed (see F4).

---

### F13 — `audit_workspace.sh` reports empty dirs as errors but doesn't show gitkeep status (LOW)

**File:** `scripts/audit_workspace.sh:23-29, 36-38`

The script counts empty directories and lists them, exiting 2 if any are empty. But the empty-dir list does not distinguish between:
- A real "directory with no files" (legitimate issue)
- A "directory with only `.gitkeep`" (allowed by `.devin/hooks.json::requireEmptyDirsToHaveGitkeep: true`)

A directory containing just `.gitkeep` is **not** empty (`ls -A` returns `.gitkeep`), so this script won't list it. But the script's exit code 2 conflates "empty" with "broken". If `validate-workspace.sh` (which checks `.gitkeep` presence) is the authoritative check, then `audit_workspace.sh` is providing overlapping-but-different information.

**Recommendation:** Either (a) make `audit_workspace.sh` purely informational and exit 0 always, or (b) extend it to also verify `.gitkeep` presence and deduplicate with `validate-workspace.sh`.

---

### F14 — `rebuild_python_with_ssl.sh` uses `read -p` which is bash-only (LOW)

**File:** `scripts/rebuild_python_with_ssl.sh:11`

`read -p "Proceed? [y/N] " confirm` is a bash extension. The shebang is `#!/usr/bin/env bash` so this is fine for the declared shell, but if anyone sources the script from a `sh` context, `read -p` fails. Not a real issue given the shebang.

**Recommendation:** Document the bash-only nature in a comment.

---

### F15 — `warmup_apparat.py` and `profile_apparat.py` have duplicate path-bootstrap boilerplate (LOW)

**Files:** `scripts/warmup_apparat.py:11-19` and `scripts/profile_apparat.py:6-12`

Both scripts have identical 4-line path-bootstrap:
```python
current_dir = Path(__file__).resolve().parent
mangrove_dir = current_dir.parent
platform_dir = mangrove_dir / "mangrove_platform"
mcp_dir = platform_dir / "mcp"
for d in (str(mcp_dir), str(platform_dir), str(mangrove_dir)):
    if d not in sys.path:
        sys.path.insert(0, d)
```

The cleanest fix would be to use the package layout (`scripts/__init__.py` already exists): make `warmup_apparat` and `profile_apparat` importable as `scripts.warmup_apparat` and `scripts.profile_apparat` via the project's `pythonpath = ["mangrove_platform"]` plus a `scripts` package discovery. Then the path bootstrap is unnecessary.

**Recommendation:** Rely on package import once the scripts are runnable as modules (the `pyproject.toml` already has `pythonpath = ["mangrove_platform"]`; consider adding `scripts` to the wheel packages or running with `uv run python -m scripts.warmup_apparat`).

---

### F16 — No tests for any script (TESTING)

There is no `tests/test_scripts.py` or equivalent. None of the 18 scripts is unit-tested. The closest test is `tests/test_dependency_hygiene.py` (in the package) which validates dep metadata, not script behavior.

**Recommendation:** Add a minimal `tests/scripts/test_validate_lib.py` and `tests/scripts/test_check_secrets.py` for the highest-value scripts. Bash testing via `bats` (https://github.com/bats-core/bats-core) is the standard.

---

### F17 — `__init__.py` is one-liner; scripts are not importable as a package (DOCS)

**File:** `scripts/__init__.py:1`

```python
"""Mangrove scripts package."""
```

But the scripts use `from apparat.horizontal_texture_processor import ...` (e.g., `warmup_apparat.py:22-24`) which only works because of the manual `sys.path.insert(0, ...)` calls. If you ran `uv run python -m scripts.warmup_apparat`, the `from apparat...` would fail because `apparat` is inside `mangrove_platform` (not a top-level package).

**Recommendation:** Either (a) make `scripts/` a real subpackage with relative imports, or (b) update the `pythonpath` in `pyproject.toml` to include both `mangrove_platform` and the project root, so the absolute `from apparat...` works without manual path manipulation.

---

### F18 — `validate-workspace.sh` exit 0 even with warnings (LOW)

**File:** `scripts/validate-workspace.sh:185-188`

```bash
elif [ $warnings -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Validation completed with $warnings warning(s)$${NC}"
    exit 0
```

When warnings are present, the script exits 0. This means CI's `workspace-validation` job passes even with warnings. Combined with F1 (the unused validate-lib), this means the workspace-validation job is essentially advisory. If a hook reports "Python cache directories found in project" or "No virtual environment found", CI does not block.

**Recommendation:** Decide policy: should warnings fail the job? If yes, change to `exit 1` when warnings > 0; if no, document the decision.

---

## Summary by severity

| Severity | Count | Findings |
|---|---|---|
| CRITICAL | 4 | F1, F2, F3, F4 |
| HIGH | 2 | F5, F6 |
| MEDIUM | 4 | F7, F8, F9, F10 |
| LOW | 7 | F11, F12, F13, F14, F15, F17, F18 |
| TESTING | 1 | F16 |

**Top 4 to address immediately:**
1. **F1 — `validate-lib.sh` is dead code.** Either adopt it or delete it.
2. **F2, F3, F4 — Three scripts (`attribution_oscillator.py`, `browser_global_assistance_audit.py`, `branch-audit.sh`) are theater/dead/stub.** Remove.
3. **F5 — `guardrail_heatmap.py` heuristic checks required imports.** Remove or rewrite.
4. **F6 — `build_factbook.py` reads from a path that doesn't exist on this host.** Add a mount-check guard.
