#!/usr/bin/env bash
# ==============================================================================
# Script Name: validate-lib.sh
# Description: Shared validation library containing logging helpers and configuration initialization
# Scope/Safety: Safe / Read-only helper module
# Dependencies: bash builtins
# ==============================================================================

# Note: this script is intended to be sourced by the individual check scripts.
# Callers (4): check-secrets.sh, check-large-files.sh, check-forbidden-patterns.sh,
# validate-workspace.sh — all source this on line 8. Do not delete without
# updating each consumer to inline its own counter / color variables.

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
COMPLIANCE_DIR_DEFAULT='.compliance-hand-off'
STALE_BRANCH_AGE_DAYS_DEFAULT=90
SECRET_PATTERNS_REGEX_DEFAULT='password\s*=\s*[''"]|api[_-]?key\s*=\s*[''"]|secret\s*=\s*[''"]|token\s*=\s*[''"]|credential\s*=\s*[''"]|aws[_-]?access[_-]?key\s*=|private[_-]?key\s*=|bearer\s+[A-Za-z0-9_\-\.]+'

# exported variables
MAX_SIZE_KB="${MAX_SIZE_KB_DEFAULT}"
FORBIDDEN_DOMAINS="${FORBIDDEN_DOMAINS_DEFAULT}"
FORBIDDEN_TOKENS="${FORBIDDEN_TOKENS_DEFAULT}"
EXCLUDE_FILES="${EXCLUDE_FILES_DEFAULT}"
COMPLIANCE_DIR="${COMPLIANCE_DIR_DEFAULT}"
STALE_BRANCH_AGE_DAYS="${STALE_BRANCH_AGE_DAYS_DEFAULT}"
SECRET_PATTERNS_REGEX="${SECRET_PATTERNS_REGEX_DEFAULT}"

FIND_EXCLUDES=(
    ! -path "./.venv/*" 
    ! -path "./venv/*" 
    ! -path "./.git/*" 
    ! -path "./htmlcov/*" 
    ! -path "./.mypy_cache/*" 
    ! -path "./.opencode/*" 
    ! -path "./.pytest_cache/*" 
    ! -path "./.devin/*" 
    ! -path "*/mangrove_platform/apparat/phase_handlers.py"
)

# Counters (scripts can rely on these names)
errors=0
warnings=0
violations_found=0

report_error() {
    echo -e "${RED}[ERROR] $1${NC}"
    errors=$((errors + 1))
}

report_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
    warnings=$((warnings + 1))
}

report_success() {
    echo -e "${GREEN}[OK] $1${NC}"
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
            COMPLIANCE_DIR=$(jq -r '.environment.complianceDirectory // ".compliance-hand-off"' "$config_file" 2>/dev/null || echo "$COMPLIANCE_DIR_DEFAULT")
            STALE_BRANCH_AGE_DAYS=$(jq -r '.environment.staleBranchAgeDays // 90' "$config_file" 2>/dev/null || echo "$STALE_BRANCH_AGE_DAYS_DEFAULT")
            local has_secret_patterns
            has_secret_patterns=$(jq -r 'has("environment") and (.environment | has("secretPatterns"))' "$config_file" 2>/dev/null || echo false)
            if [ "$has_secret_patterns" = "true" ]; then
                SECRET_PATTERNS_REGEX=$(jq -r '.environment.secretPatterns | join("|")' "$config_file" 2>/dev/null || echo "$SECRET_PATTERNS_REGEX_DEFAULT")
            fi
        else
            report_warning "jq not available — using defaults for validation config"
            COMPLIANCE_DIR="${COMPLIANCE_DIR_DEFAULT}"
            STALE_BRANCH_AGE_DAYS="${STALE_BRANCH_AGE_DAYS_DEFAULT}"
            SECRET_PATTERNS_REGEX="${SECRET_PATTERNS_REGEX_DEFAULT}"
        fi
    else
        # No config file: use defaults
        MAX_SIZE_KB="${MAX_SIZE_KB_DEFAULT}"
        FORBIDDEN_DOMAINS="${FORBIDDEN_DOMAINS_DEFAULT}"
        FORBIDDEN_TOKENS="${FORBIDDEN_TOKENS_DEFAULT}"
        COMPLIANCE_DIR="${COMPLIANCE_DIR_DEFAULT}"
        STALE_BRANCH_AGE_DAYS="${STALE_BRANCH_AGE_DAYS_DEFAULT}"
        SECRET_PATTERNS_REGEX="${SECRET_PATTERNS_REGEX_DEFAULT}"
    fi
}

# Small helper to check for git context
in_git_repo() {
    git rev-parse --git-dir > /dev/null 2>&1
}

# Dependency checking helper for agent-safe script execution
# Usage: check_dependencies git jq rg uv
check_dependencies() {
    local missing=()
    for cmd in "$@"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        report_error "Missing required dependencies: ${missing[*]}"
        echo "Please install missing commands before running this script"
        exit 1
    fi
}

# Load script-specific configuration from .devin/hooks.json
# Usage: get_script_config <script_name> <key>
# Example: get_script_config "guardrailHeatmap" "targetPaths.mcpServer"
get_script_config() {
    local script_name="${1-}"
    local key="${2-}"
    local config_file=".devin/hooks.json"

    if [ -z "$script_name" ] || [ -z "$key" ]; then
        echo ""
        return
    fi

    if [ -f "$config_file" ] && command -v jq >/dev/null 2>&1; then
        jq -r ".scriptConfig.${script_name}.${key} // empty" "$config_file" 2>/dev/null || echo ""
    else
        echo ""
    fi
}
