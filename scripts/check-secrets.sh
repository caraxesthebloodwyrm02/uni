#!/usr/bin/env bash
# check-secrets.sh - Check for potential secrets in code files
# Prevents accidental commits of credentials, API keys, or sensitive data

set -euo pipefail

# Source shared validation library
. scripts/validate-lib.sh

# Initialize configuration
init_validation ".devin/hooks.json"

# Common secret patterns
SECRET_PATTERNS=(
    "password\s*=\s*['\"]"         # password = "..." or password = '...'
    "api[_-]?key\s*=\s*['\"]"      # api_key = "..." or api_key = '...'
    "secret\s*=\s*['\"]"          # secret = "..." or secret = '...'
    "token\s*=\s*['\"]"           # token = "..." or token = '...'
    "credential\s*=\s*['\"]"      # credential = "..." or credential = '...'
    "aws[_-]?access[_-]?key\s*="   # AWS access key
    "private[_-]?key\s*="          # Private key
    "bearer\s+[A-Za-z0-9_\-\.]+"  # Bearer token
)

echo "Checking for potential secrets..."

# Check staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
if [ -z "$staged_files" ]; then
    report_success "No staged files to check"
    exit 0
fi

suspicious_files=$(echo "$staged_files" | while read file; do
    if [ -f "$file" ]; then
        for pattern in "${SECRET_PATTERNS[@]}"; do
            if grep -qiE "$pattern" "$file" 2>/dev/null; then
                echo "$file (matches pattern: $pattern)"
                break
            fi
        done
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
