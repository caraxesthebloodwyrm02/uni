#!/usr/bin/env bash
# ==============================================================================
# Script Name: audit_workspace.sh
# Description: Scan workspace directories to find and report empty folders
# Scope/Safety: Safe / Read-only
# Dependencies: find, ls
# ==============================================================================

set -euo pipefail

# Check dependencies
for cmd in find ls; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: Required dependency '$cmd' is not installed or not in PATH." >&2
        exit 1
    fi
done

if [[ $# -ge 1 ]]; then
    ROOT="$1"
else
    # scripts/audit_workspace.sh → derive workspace root from $0
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

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
done < <(find "${ROOT}" -type d -not -path "*/.git*" -not -path "*/.venv*" -not -path "*/.*_cache*" -print0)

echo "================================"
echo "Total directories: ${total_dirs}"
echo "Empty directories: ${empty_count}"

# Script is purely informational; validate-workspace.sh enforces .gitkeep policies.
exit 0
