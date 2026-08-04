#!/usr/bin/env bash
# ==============================================================================
# Script Name: measure-pr-impact.sh
# Description: Track complexity and impact metrics for open Dependabot pull requests
# Scope/Safety: Safe / Read-only GitHub API querying, creates local log folder
# Dependencies: git, sed, gh, wc, jq, mkdir
# ==============================================================================

set -e

# Check dependencies
for cmd in git sed gh wc jq mkdir; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: Required dependency '$cmd' is not installed or not in PATH." >&2
        if [ "$cmd" = "gh" ]; then
            echo "Install GitHub CLI (gh) from: https://cli.github.com/" >&2
        fi
        exit 1
    fi
done

echo "=== Dependency PR Impact Measurement ==="
echo "Date: $(date)"
echo ""

# Get repository name
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com\///' | sed 's/\.git$//' || echo "unknown")

if [ "$REPO" = "unknown" ]; then
    echo "Error: Could not determine repository name"
    exit 1
fi

echo "Repository: $REPO"
echo ""

echo "=== Analyzing Dependency PRs ==="
echo ""

# Get all open dependency PRs
PRS=$(gh pr list --state open --label dependencies --json number --repo "$REPO" --jq '.[].number' 2>/dev/null)

if [ -z "$PRS" ]; then
    echo "No open dependency PRs found"
    exit 0
fi

echo "Found $(echo $PRS | wc -w) open dependency PRs"
echo ""

# Analyze each PR
for pr in $PRS; do
    echo "--- PR #$pr ---"
    
    # Get PR details
    DETAILS=$(gh pr view $pr --json title,additions,deletions,changedFiles,mergeable,mergeStateStatus --repo "$REPO" 2>/dev/null)
    
    TITLE=$(echo $DETAILS | jq -r '.title')
    ADDITIONS=$(echo $DETAILS | jq '.additions')
    DELETIONS=$(echo $DETAILS | jq '.deletions')
    CHANGED_FILES=$(echo $DETAILS | jq '.changedFiles')
    MERGEABLE=$(echo $DETAILS | jq -r '.mergeable')
    MERGE_STATUS=$(echo $DETAILS | jq -r '.mergeStateStatus')
    
    echo "Title: $TITLE"
    echo "Lines added: $ADDITIONS"
    echo "Lines deleted: $DELETIONS"
    echo "Files changed: $CHANGED_FILES"
    echo "Mergeable: $MERGEABLE"
    echo "Merge status: $MERGE_STATUS"
    
    # Calculate complexity score
    TOTAL_CHANGES=$((ADDITIONS + DELETIONS))
    if [ $TOTAL_CHANGES -lt 50 ]; then
        COMPLEXITY="low"
    elif [ $TOTAL_CHANGES -lt 200 ]; then
        COMPLEXITY="medium"
    else
        COMPLEXITY="high"
    fi
    echo "Complexity: $COMPLEXITY"
    echo ""
    
    # Save PR metrics
    mkdir -p .dependency-pr-metrics
    echo "$DETAILS" > ".dependency-pr-metrics/pr_$pr.json"
done

echo "=== Summary ==="
echo "Total PRs analyzed: $(echo $PRS | wc -w)"
echo "Metrics saved to: .dependency-pr-metrics/"
echo ""
echo "Recommendations:"
echo "- Low complexity PRs (<50 lines): Consider auto-merge if CI passes"
echo "- Medium complexity PRs (50-200 lines): Manual review recommended"
echo "- High complexity PRs (>200 lines): Manual review required"
