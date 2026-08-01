#!/usr/bin/env bash
# check-secrets.sh - Check for potential secrets in code files
# Prevents accidental commits of credentials, API keys, or sensitive data

set -euo pipefail

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

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Checking for potential secrets..."

# Check staged files
suspicious_files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | while read file; do
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
    echo -e "${RED}✗ Potential secrets detected:${NC}"
    echo "$suspicious_files"
    echo -e "${YELLOW}Please review these files before committing${NC}"
    echo -e "${YELLOW}If these are false positives, use 'git commit --no-verify' to bypass${NC}"
    exit 1
fi

echo -e "${GREEN}✓ No potential secrets found${NC}"
exit 0