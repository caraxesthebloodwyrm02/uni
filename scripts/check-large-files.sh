#!/usr/bin/env bash
# ==============================================================================
# Script Name: check-large-files.sh
# Description: Check staged files for size limit compliance
# Scope/Safety: Safe / Read-only pre-commit validation
# Dependencies: git, du, cut
# ==============================================================================

set -euo pipefail

# Source shared validation library
. scripts/validate-lib.sh

# Initialize configuration
init_validation ".devin/hooks.json"

# Check dependencies for agent-safe execution
check_dependencies git du cut

echo "Checking for large files..."

# Check staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
if [ -z "$staged_files" ]; then
    report_success "No staged files to check"
    exit 0
fi

large_files=$(echo "$staged_files" | while IFS= read -r file; do
    if [ -f "$file" ]; then
        size=$(du -k "$file" | cut -f1)
        if [ "$size" -gt "$MAX_SIZE_KB" ]; then
            echo "$file ($size KB)"
        fi
    fi
done)

if [ -n "$large_files" ]; then
    report_error "Large files detected:"
    echo "$large_files"
    report_warning "Maximum size: ${MAX_SIZE_KB}KB for code files"
    exit 1
fi

report_success "No large files found"
exit 0
