# Compliance Baseline — Hand-off Plan (deferred)

This directory captures the compliance-baseline strategy in deferred state.

## Status

**Phase execution deferred by operator, 2026-07-31.**

- `compliance_baseline` phase is **registered** in `platform/apparat/sisa.py`
  (PHASE_DEFINITIONS) and **resolves** in the SISA bootstrap (12/12 phases).
- The handler `compliance_baseline_handler` in `platform/apparat/phase_handlers.py`
  is **not invoked** — no LICENSE, NOTICE, or TERMS_OF_ENGAGEMENT.md has been
  written to the live tree.
- This deferral is reversible: invoking the phase materialises the trio at the
  apparat parent root (default: `/home/cable/series/mangrove/`).

## Why deferred

The operator's standing directive is to surface gaps and produce an actionable
strategy. The compliance baseline is **present as a plan**, not as artefacts,
because the operator chose to defer materialisation. The reasons offered:

- The live tree is documented as a stub. Materialising Apache-2.0 LICENSE in a stub
  is technically legal but creates an attestation that the canonical archive
  may not yet reflect.
- The canonical archive at `/home/irfankabir/` (volume UUID `cf656878-…`) is
  not mounted. A clean canonical-port relies on the canonical tree being
  readable first.
- Two stale references in `mangrove/CLAUDE.md` (line 154 to `~/.claude/AGREEMENT.md`
  and line 179 to `finance/DO-NOT.html`) predate the live-stub era and were
  deferred alongside the staging.

## How to materialise

```bash
# 1. Confirm the handler is registered
uv run --python /home/cable/.local/bin/python3.13 \
  python platform/apparat/sisa.py --list-phases
# expect: compliance_baseline on the list

# 2. Invoke the phase (writes LICENSE, NOTICE, TERMS_OF_ENGAGEMENT.md)
uv run --python /home/cable/.local/bin/python3.13 \
  python -c "
import importlib.util as u
spec = u.spec_from_file_location('a', 'platform/apparat/apparat.py')
m = u.module_from_spec(spec); spec.loader.exec_module(m)
spec2 = u.spec_from_file_location('p', 'platform/apparat/phase_handlers.py')
p = u.module_from_spec(spec2); spec2.loader.exec_module(p)
m.register_phase_handler('compliance_baseline')(p.compliance_baseline_handler)
class Stub: pass
proc = Stub(); proc.ipo = Stub()
print('OK' if m.get_phase_handler('compliance_baseline')(proc) else 'FAIL')
"

# 3. Verify the three files exist
ls -la /home/cable/series/mangrove/{LICENSE,NOTICE,TERMS_OF_ENGAGEMENT.md}
```

## Accumulated hand-off policy (canonical port)

When `/home/irfankabir/` becomes mounted, the hand-off shape is **accumulated
delta**:

- Ship only files changed since the prior sync, not a full-tree overwrite.
- Log every change in `.compliance-hand-off/.audit.log` (this directory).
- Use `rsync --update --times` (or equivalent) so unchanged files are not
  re-touched. The `.audit.log` then becomes the source of truth for what was
  sent when.

Skeleton (verbatim, replace `<canonical-mangrove-path>` with the actual mount
path once the volume is up):

```bash
rsync -av --update \
  --include='LICENSE' \
  --include='NOTICE' \
  --include='TERMS_OF_ENGAGEMENT.md' \
  --include='.compliance-hand-off/' \
  --exclude='*' \
  /home/cable/series/mangrove/ \
  /home/irfankabir/<canonical-mangrove-path>/
```

## Conventional commit (when / if staging opens)

```
chore(license): add LICENSE, NOTICE, TERMS_OF_ENGAGEMENT.md via apparat compliance_baseline

- Materialise Apache-2.0 LICENSE file at repo root matching pyproject.toml:11.
- Update all compliance references to Apache-2.0 License.
- Materialise TERMS_OF_ENGAGEMENT.md consolidating in-force memory entries.
- Handler: platform/apparat/phase_handlers.py::compliance_baseline_handler.
- Phase registration: platform/apparat/sisa.py::PHASE_DEFINITIONS.
- Deferred per operator instruction; see .compliance-hand-off/README.md.
```

Stage explicit paths only — never `git add -A` / `git add .`.

## Decision log

| # | Decision | Source | Notes |
|---|---|---|---|
| 1 | Stage live tree? | Operator: "Skip — defer" | No files written this run |
| 2 | PEP form change? | Operator: "check" | Verified PEP 639 (current = `{ text = "Apache-2.0" }`) and PEP 735 (`[dependency-groups]` already correct); no Edit applied |
| 3 | Canonical hand-off? | Operator: "accumulated" | Interpreted as accumulated-delta rsync with audit log; rsync skeleton above |
| 4 | Stale CLAUDE.md refs? | Auto-deferred | `~/.claude/AGREEMENT.md` and `finance/DO-NOT.html` are dead-on-arrival; addressing them is bigger than the compliance-baseline scope. Defer to canonical-port |
| 5 | Build backend | Verified live | `[build-system]` is `hatchling` (PEP 639-capable) — no blocker for future SPDX-form migration |
| 6 | Volume state | Verified live | `cf656878-…` unmounted; canonical archive unreachable; hand-off is blocked-on-mount |
