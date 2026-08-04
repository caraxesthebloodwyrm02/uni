#!/usr/bin/env bash
# check-forbidden-patterns.sh - Check for forbidden domains and tokens (3PAA-SHADOW containment)
# This script checks code files for forbidden patterns per governance rules

set -euo pipefail

# Source shared validation library
. scripts/validate-lib.sh

# Initialize configuration
init_validation ".devin/hooks.json"

echo "Checking for forbidden patterns (3PAA-SHADOW containment)..."

# The shared lib provides EXCLUDE_FILES, FORBIDDEN_DOMAINS, and FORBIDDEN_TOKENS

# Determine if we're in a git context
if in_git_repo; then
    # Git context - check staged files
    staged_files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)
    if [ -z "$staged_files" ]; then
        report_success "No staged files to check"
        exit 0
    fi

    forbidden_domains=$(echo "$staged_files" | grep -v -E "$EXCLUDE_FILES" | xargs grep -lE "$FORBIDDEN_DOMAINS" 2>/dev/null || true)
    if [ -n "$forbidden_domains" ]; then
        report_error "Forbidden domains detected (3PAA-SHADOW containment)"
        echo "Forbidden domains: $FORBIDDEN_DOMAINS"
        violations_found=$((violations_found + 1))
    else
        report_success "No forbidden domains found"
    fi

    # Check files for forbidden tokens
    forbidden_tokens=$(echo "$staged_files" | grep -v -E "$EXCLUDE_FILES" | xargs grep -lE "$FORBIDDEN_TOKENS" 2>/dev/null || true)
    if [ -n "$forbidden_tokens" ]; then
        report_error "Forbidden tokens detected (3PAA-SHADOW containment)"
        echo "Forbidden tokens: $FORBIDDEN_TOKENS"
        violations_found=$((violations_found + 1))
    else
        report_success "No forbidden tokens found"
    fi

    # Check working directory for violations (not staged)
    unstaged_files=$(git diff --name-only 2>/dev/null || true)
    if [ -z "$unstaged_files" ]; then
        report_success "No unstaged files to check"
    else
        unstaged_violations=$(echo "$unstaged_files" | grep -v -E "$EXCLUDE_FILES" | xargs grep -lE "$FORBIDDEN_DOMAINS|$FORBIDDEN_TOKENS" 2>/dev/null || true)
        if [ -n "$unstaged_violations" ]; then
            report_warning "Forbidden patterns found in unstaged files. Stage changes to check them properly."
        fi
    fi
else
    # Non-git context (CI validation) - check all files
    forbidden_domains=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
        ! -path "./.venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
        ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" \
        -exec grep -lE "$FORBIDDEN_DOMAINS" {} \; 2>/dev/null || true)
    if [ -n "$forbidden_domains" ]; then
        report_error "Forbidden domains detected (3PAA-SHADOW containment)"
        echo "Forbidden domains: $FORBIDDEN_DOMAINS"
        violations_found=$((violations_found + 1))
    else
        report_success "No forbidden domains found"
    fi

    forbidden_tokens=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
        ! -path "./.venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
        ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" \
        -exec grep -lE "$FORBIDDEN_TOKENS" {} \; 2>/dev/null || true)
    if [ -n "$forbidden_tokens" ]; then
        report_error "Forbidden tokens detected (3PAA-SHADOW containment)"
        echo "Forbidden tokens: $FORBIDDEN_TOKENS"
        violations_found=$((violations_found + 1))
    else
        report_success "No forbidden tokens found"
    fi
fi

if [ $violations_found -gt 0 ]; then
    report_error "Security policy violation detected (3PAA-SHADOW containment)"
    exit 1
fi

report_success "All security checks passed"
exit 0
