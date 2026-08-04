#!/usr/bin/env bash
# ==============================================================================
# Script Name: prune-stale-branches.sh
# Description: Generate a CSV audit report indicating remote branches that are stale or merged
# Scope/Safety: Safe / Read-only git queries, writes report to compliance folder
# Dependencies: git, mkdir, date, grep
# ==============================================================================

set -euo pipefail

# Check dependencies
for dep in git mkdir date grep; do
    command -v "$dep" >/dev/null 2>&1 || { echo "missing dependency: $dep" >&2; exit 1; }
done

COMPLIANCE_DIR=".compliance-hand-off"
STALE_BRANCH_AGE_DAYS=90

OUT_DIR="${COMPLIANCE_DIR}"
OUT_FILE="$OUT_DIR/branch-audit.csv"
mkdir -p "$OUT_DIR"

echo "fetching remotes..."
git fetch origin --prune 2>/dev/null || echo "Git fetch failed (read-only filesystem), using local refs"

# Header
echo "branch,last_commit_iso,last_commit_sha,is_merged_into_main,recommendation" > "$OUT_FILE"

# For each remote branch (excluding HEAD), get last commit date and whether merged into origin/main
while IFS= read -r ref; do
    # Extract branch name without refs/remotes/origin/ prefix
    branch=${ref#refs/remotes/origin/}
    # skip HEAD and main reference
    if [ "$branch" = "HEAD" ] || [ "$branch" = "main" ]; then
        continue
    fi
    sha=$(git rev-parse --verify "$ref" 2>/dev/null || echo "unknown")
    date_iso=$(git show -s --format=%ci "$sha" 2>/dev/null || echo "unknown")
    
    # check merged status using merge-base --is-ancestor
    if git merge-base --is-ancestor origin/main "$ref" 2>/dev/null; then
        merged=true
    else
        merged=false
    fi

    # Recommend deletion if merged==true, or if older than 90 days
    rec="keep"
    if [ "$merged" = true ]; then
        rec="delete (merged)"
    else
        # compute age in days
        commit_epoch=$(git show -s --format=%ct "$sha" 2>/dev/null || echo "0")
        now_epoch=$(date +%s)
        age_days=$(( (now_epoch - commit_epoch) / 86400 ))
        if [ $age_days -ge "${STALE_BRANCH_AGE_DAYS}" ]; then
            rec="stale (>=${STALE_BRANCH_AGE_DAYS}d)"
        fi
    fi

    echo "\"${branch}\",\"${date_iso}\",\"${sha}\",\"${merged}\",\"${rec}\"" >> "$OUT_FILE"
done < <(git for-each-ref --format='%(refname)' refs/remotes/origin 2>/dev/null | grep -v '\->' || true)

echo "Audit written to $OUT_FILE"
