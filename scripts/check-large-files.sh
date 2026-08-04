#!/usr/bin/env bash
# check-large-files.sh - Check for files that exceed size limits
# Prevents accidental commits of large files

set -euo pipefail

# Source shared validation library
. scripts/validate-lib.sh

# Initialize configuration
init_validation ".devin/hooks.json"

echo "Checking for large files..."

# Check staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
if [ -z "$staged_files" ]; then
    report_success "No staged files to check"
    exit 0
fi

large_files=$(echo "$staged_files" | while read file; do
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
