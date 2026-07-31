#!/usr/bin/env bash
# audit_workspace.sh — count empty directories and list them under /home/cable/series/mangrove.
# Stub: real audit will be wired in Phase 2.
#
# Usage: bash scripts/audit_workspace.sh [root]
# Default root: /home/cable/series/mangrove

set -euo pipefail

ROOT="${1:-/home/cable/series/mangrove}"

echo "Workspace audit — root: ${ROOT}"
echo "================================"

if [[ ! -d "${ROOT}" ]]; then
    echo "ERROR: root does not exist: ${ROOT}" >&2
    exit 1
fi

empty_count=0
total_dirs=0

while IFS= read -r -d '' dir; do
    total_dirs=$((total_dirs + 1))
    if [[ -z "$(ls -A "${dir}" 2>/dev/null)" ]]; then
        empty_count=$((empty_count + 1))
        echo "  EMPTY: ${dir#${ROOT}/}"
    fi
done < <(find "${ROOT}" -type d -print0)

echo "================================"
echo "Total directories: ${total_dirs}"
echo "Empty directories: ${empty_count}"

# Exit non-zero if any dir is empty — caller can decide policy.
if [[ "${empty_count}" -gt 0 ]]; then
    exit 2
fi
