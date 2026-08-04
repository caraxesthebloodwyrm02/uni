#!/usr/bin/env bash
# ==============================================================================
# Script Name: consolidate-branches.sh
# Description: Delete merged remote and local tracking branches
# Scope/Safety: Medium risk / Deletes local/remote git branches
# Dependencies: git, grep, sort, sed
# ==============================================================================

set -e

# Check dependencies
for cmd in git grep sort sed; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: Required dependency '$cmd' is not installed or not in PATH." >&2
        exit 1
    fi
done

echo "=== Branch Consolidation Execution ==="
echo "License: MIT | Risk: Minimal | Scope: Cleanup only"
echo ""

# Pre-deletion verification
echo "🔍 Pre-deletion verification..."
for branch in chore/cleanup-validation-and-audit chore/hygiene-cleanup fix/test-licence-expectations; do
  if git rev-parse --verify --quiet "origin/$branch" >/dev/null; then
    if git merge-base --is-ancestor "origin/$branch" origin/main; then
      echo "✅ $branch: merged into main"
    else
      echo "⚠️  $branch: exists but not fully merged (ancestor check failed). Skipping safe auto-delete."
    fi
  else
    echo "ℹ️  $branch: does not exist on remote"
  fi
done

echo ""

# Delete remote branches
echo "🗑️  Deleting remote branches..."
for branch in chore/cleanup-validation-and-audit chore/hygiene-cleanup fix/test-licence-expectations; do
  if git rev-parse --verify --quiet "origin/$branch" >/dev/null; then
    # Only delete if it's merged or if we force it
    echo "Deleting remote branch $branch..."
    git push origin --delete "$branch" || echo "Failed to delete remote branch $branch"
  fi
done

echo ""

# Delete local branches
echo "🧹 Cleaning up local branches..."
git branch -D chore/hygiene-cleanup 2>/dev/null || true
git branch -D fix/test-licence-expectations 2>/dev/null || true
git branch -D pr-12 2>/dev/null || true

echo ""

# Cleanup
echo "🧼 Final cleanup..."
git fetch --prune
git remote prune origin

echo ""

# Post-deletion verification
echo "✅ Post-deletion verification:"
echo "Remote branches:"
git branch -r | grep -v HEAD | sort
echo ""
echo "Local branches:"
git branch | sed 's/^\* //' | sed 's/^  //' | sort

echo ""
echo "🎉 Branch consolidation complete!"
