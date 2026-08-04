#!/usr/bin/env bash
# ==============================================================================
# Script Name: track-dependencies.sh
# Description: Track dependency update statistics and export metrics to JSON
# Scope/Safety: Safe / Read-only package/PR checking, writes dependency-metrics.json
# Dependencies: git, sed, date (optional: gh, jq, uv)
# ==============================================================================

set -e

# Check dependencies
for cmd in git sed date; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: Required dependency '$cmd' is not installed or not in PATH." >&2
        exit 1
    fi
done

echo "=== Dependency Update Metrics ==="
echo "Date: $(date)"
echo ""

# Get repository name from git remote
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com\///' | sed 's/\.git$//' || echo "unknown")

if [ "$REPO" = "unknown" ]; then
    echo "Warning: Could not determine repository name from git remote"
    echo "Skipping GitHub API calls - will run local checks only"
    HAS_GH=false
elif ! command -v gh &> /dev/null; then
    echo "Warning: GitHub CLI (gh) is not installed - running local checks only"
    HAS_GH=false
elif ! command -v jq &> /dev/null; then
    echo "Warning: jq is not installed - running local checks only (needed for PR tracking)"
    HAS_GH=false
else
    HAS_GH=true
fi

echo "Repository: $REPO"
echo ""

# Local dependency count (always runs)
echo "=== Local Dependency State ==="
DEP_COUNT="0"
if command -v uv &> /dev/null; then
    echo "Current dependencies:"
    uv pip list 2>/dev/null || echo "uv pip list failed"
    DEP_COUNT=$(uv pip list 2>/dev/null | grep -c "" || echo "0")
    echo "Total dependencies: $DEP_COUNT"
else
    echo "uv not found - skipping dependency list"
fi
echo ""

# GitHub API calls (if gh available)
if [ "$HAS_GH" = true ]; then
    echo "=== Open Dependency PRs ==="
    gh pr list --state open --label dependencies --json number,title,createdAt,mergeable,mergeStateStatus --repo "$REPO" 2>/dev/null || echo "No open dependency PRs or GitHub API error"
    echo ""

    echo "=== Recent Dependency Merges (last 10) ==="
    gh pr list --state closed --label dependencies --json number,title,closedAt --merged --limit 10 --repo "$REPO" 2>/dev/null || echo "No recent dependency merges or GitHub API error"
    echo ""

    echo "=== PR Count Summary ==="
    OPEN_COUNT=$(gh pr list --state open --label dependencies --json number --repo "$REPO" 2>/dev/null | jq 'length' || echo "0")
    CLOSED_COUNT=$(gh pr list --state closed --label dependencies --json number --repo "$REPO" 2>/dev/null | jq 'length' || echo "0")
    echo "Open dependency PRs: $OPEN_COUNT"
    echo "Closed dependency PRs (all time): $CLOSED_COUNT"
else
    echo "=== GitHub API ==="
    echo "GitHub CLI not available - skipping remote PR tracking"
    echo "Install gh CLI to enable: https://cli.github.com/"
fi

echo ""
echo "=== Data Collection Complete ==="
echo "Metrics saved to: .dependency-metrics.json"

# Save metrics to JSON
METRICS_FILE=".dependency-metrics.json"
cat > "$METRICS_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "repository": "$REPO",
  "local_dep_count": "$DEP_COUNT",
  "has_github_cli": "$HAS_GH",
  "phase": "1-monitoring"
}
EOF

echo "Stored metrics in $METRICS_FILE"
