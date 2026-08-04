#!/usr/bin/env bash
# ==============================================================================
# Script Name: check-secrets.sh
# Description: Check staged files for potential credentials, API keys, and secrets
# Scope/Safety: Safe / Read-only pre-commit validation
# Dependencies: git, grep
# ==============================================================================

set -euo pipefail

# Source shared validation library
. scripts/validate-lib.sh

# Initialize configuration
init_validation ".devin/hooks.json"

# Check dependencies for agent-safe execution
check_dependencies git grep

echo "Checking for potential secrets..."

# Check staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
if [ -z "$staged_files" ]; then
    report_success "No staged files to check"
    exit 0
fi

suspicious_files=$(echo "$staged_files" | while read file; do
    if [ -f "$file" ]; then
        if grep -qiE "$SECRET_PATTERNS_REGEX" "$file" 2>/dev/null; then
            echo "$file"
        fi
    fi
done)

if [ -n "$suspicious_files" ]; then
    report_error "Potential secrets detected:"
    echo "$suspicious_files"
    report_warning "Please review these files before committing"
    report_warning "If these are false positives, use 'git commit --no-verify' to bypass"
    exit 1
fi

report_success "No potential secrets found"
exit 0
