#!/usr/bin/env bash
# check-forbidden-patterns.sh - Check for forbidden domains and tokens (3PAA-SHADOW containment)
# This script checks code files for forbidden patterns per governance rules

set -euo pipefail

# Forbidden patterns per 3PAA-SHADOW containment
FORBIDDEN_DOMAINS="factory\.ai|cursor\.com|cursor\.sh|workos\.com"
FORBIDDEN_TOKENS="WorkOS|Factory"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Checking for forbidden patterns (3PAA-SHADOW containment)..."

# Exclude governance documentation files
EXCLUDE_FILES="mangrove_platform/apparat/phase_handlers.py|.devin/"

violations_found=0

# Determine if we're in a git context
if git rev-parse --git-dir > /dev/null 2>&1; then
    # Git context - check staged files
    # Check files for forbidden domains
    forbidden_domains=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep -v -E "$EXCLUDE_FILES" | xargs grep -lE "$FORBIDDEN_DOMAINS" 2>/dev/null || true)
    if [ -n "$forbidden_domains" ]; then
        echo -e "${RED}✗ Forbidden domains detected (3PAA-SHADOW containment)${NC}"
        echo "Forbidden domains: $FORBIDDEN_DOMAINS"
        violations_found=$((violations_found + 1))
    else
        echo -e "${GREEN}✓ No forbidden domains found${NC}"
    fi

    # Check files for forbidden tokens
    forbidden_tokens=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep -v -E "$EXCLUDE_FILES" | xargs grep -lE "$FORBIDDEN_TOKENS" 2>/dev/null || true)
    if [ -n "$forbidden_tokens" ]; then
        echo -e "${RED}✗ Forbidden tokens detected (3PAA-SHADOW containment)${NC}"
        echo "Forbidden tokens: $FORBIDDEN_TOKENS"
        violations_found=$((violations_found + 1))
    else
        echo -e "${GREEN}✓ No forbidden tokens found${NC}"
    fi

    # Check working directory for violations (not staged)
    unstaged_violations=$(git diff --name-only 2>/dev/null | grep -v -E "$EXCLUDE_FILES" | xargs grep -lE "$FORBIDDEN_DOMAINS|$FORBIDDEN_TOKENS" 2>/dev/null || true)
    if [ -n "$unstaged_violations" ]; then
        echo -e "${YELLOW}⚠ Warning: Forbidden patterns found in unstaged files${NC}"
        echo "Stage changes to check them properly"
    fi
else
    # Non-git context (CI validation) - check all files
    # Check files for forbidden domains
    forbidden_domains=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
        ! -path "./.venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
        ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" \
        -exec grep -lE "$FORBIDDEN_DOMAINS" {} \; 2>/dev/null || true)
    if [ -n "$forbidden_domains" ]; then
        echo -e "${RED}✗ Forbidden domains detected (3PAA-SHADOW containment)${NC}"
        echo "Forbidden domains: $FORBIDDEN_DOMAINS"
        violations_found=$((violations_found + 1))
    else
        echo -e "${GREEN}✓ No forbidden domains found${NC}"
    fi

    # Check files for forbidden tokens
    forbidden_tokens=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
        ! -path "./.venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
        ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" \
        -exec grep -lE "$FORBIDDEN_TOKENS" {} \; 2>/dev/null || true)
    if [ -n "$forbidden_tokens" ]; then
        echo -e "${RED}✗ Forbidden tokens detected (3PAA-SHADOW containment)${NC}"
        echo "Forbidden tokens: $FORBIDDEN_TOKENS"
        violations_found=$((violations_found + 1))
    else
        echo -e "${GREEN}✓ No forbidden tokens found${NC}"
    fi
fi

if [ $violations_found -gt 0 ]; then
    echo -e "${RED}Security policy violation detected${NC}"
    echo "3PAA-SHADOW containment policy enforcement"
    exit 1
fi

echo -e "${GREEN}All security checks passed${NC}"
exit 0