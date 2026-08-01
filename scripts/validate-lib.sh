#!/usr/bin/env bash
# Shared validation library for workspace checks
# Provides: init_validation, color variables, report_error, report_warning, report_success

# Note: this script is intended to be sourced by the individual check scripts.

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults (can be overridden by configuration file passed to init_validation)
MAX_SIZE_KB_DEFAULT=500
FORBIDDEN_DOMAINS_DEFAULT='factory\\.ai|cursor\\.com|cursor\\.sh|workos\\.com'
FORBIDDEN_TOKENS_DEFAULT='WorkOS|Factory'
EXCLUDE_FILES_DEFAULT='mangrove_platform/apparat/phase_handlers.py|.devin/'

# exported variables
MAX_SIZE_KB="${MAX_SIZE_KB_DEFAULT}"
FORBIDDEN_DOMAINS="${FORBIDDEN_DOMAINS_DEFAULT}"
FORBIDDEN_TOKENS="${FORBIDDEN_TOKENS_DEFAULT}"
EXCLUDE_FILES="${EXCLUDE_FILES_DEFAULT}"

# Counters (scripts can rely on these names)
errors=0
warnings=0
violations_found=0

report_error() {
    echo -e "${RED}✗ $1${NC}"
    errors=$((errors + 1))
}

report_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    warnings=$((warnings + 1))
}

report_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Initialize configuration from a JSON file (optional).
# Usage: init_validation <config_file_path>
init_validation() {
    local config_file="${1-}"
    if [ -n "$config_file" ] && [ -f "$config_file" ]; then
        if command -v jq >/dev/null 2>&1; then
            MAX_SIZE_KB=$(jq -r '.environment.maxFileSizeKB // env.MAX_SIZE_KB' "$config_file" 2>/dev/null || echo "$MAX_SIZE_KB_DEFAULT")
            local has_forbidden_domains
            has_forbidden_domains=$(jq -r 'has("environment") and (.environment | has("forbiddenDomains"))' "$config_file" 2>/dev/null || echo false)
            if [ "$has_forbidden_domains" = "true" ]; then
                FORBIDDEN_DOMAINS=$(jq -r '.environment.forbiddenDomains | join("|")' "$config_file" 2>/dev/null || echo "$FORBIDDEN_DOMAINS_DEFAULT")
            fi
            local has_forbidden_tokens
            has_forbidden_tokens=$(jq -r 'has("environment") and (.environment | has("forbiddenTokens"))' "$config_file" 2>/dev/null || echo false)
            if [ "$has_forbidden_tokens" = "true" ]; then
                FORBIDDEN_TOKENS=$(jq -r '.environment.forbiddenTokens | join("|")' "$config_file" 2>/dev/null || echo "$FORBIDDEN_TOKENS_DEFAULT")
            fi
        else
            report_warning "jq not available — using defaults for validation config"
        fi
    else
        # No config file: use defaults
        MAX_SIZE_KB="${MAX_SIZE_KB_DEFAULT}"
        FORBIDDEN_DOMAINS="${FORBIDDEN_DOMAINS_DEFAULT}"
        FORBIDDEN_TOKENS="${FORBIDDEN_TOKENS_DEFAULT}"
    fi
}

# Small helper to check for git context
in_git_repo() {
    git rev-parse --git-dir > /dev/null 2>&1
}
