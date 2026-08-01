#!/usr/bin/env bash
# validate-workspace.sh - Comprehensive workspace validation
# Validates compliance with best practices, hooks, and governance rules

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Workspace Validation${NC}"
echo "=========================="

# Load configuration
CONFIG_FILE=".devin/hooks.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠ Configuration file not found: $CONFIG_FILE${NC}"
    echo "Using default configuration"
    MAX_SIZE_KB=500
    FORBIDDEN_DOMAINS="factory\.ai|cursor\.com|cursor\.sh|workos\.com"
    FORBIDDEN_TOKENS="WorkOS|Factory"
else
    echo "Loading configuration from $CONFIG_FILE"
    MAX_SIZE_KB=$(jq -r '.environment.maxFileSizeKB // 500' "$CONFIG_FILE")
    FORBIDDEN_DOMAINS=$(jq -r '.environment.forbiddenDomains[]? | join("|")' "$CONFIG_FILE" 2>/dev/null || echo "factory\.ai|cursor\.com|cursor\.sh|workos\.com")
    FORBIDDEN_TOKENS=$(jq -r '.environment.forbiddenTokens[]? | join("|")' "$CONFIG_FILE" 2>/dev/null || echo "WorkOS|Factory")
fi

errors=0
warnings=0

# Function to report errors
report_error() {
    echo -e "${RED}✗ $1${NC}"
    errors=$((errors + 1))
}

# Function to report warnings
report_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    warnings=$((warnings + 1))
}

# Function to report success
report_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

echo ""
echo "Checking workspace structure..."

# Check for stub directories without .gitkeep
echo "Checking stub directories for .gitkeep files..."
stub_dirs=("finance" "intelligence" "lab" "operations" "productivity" "workspace" "routines")
for dir in "${stub_dirs[@]}"; do
    if [ -d "$dir" ]; then
        if [ ! -f "$dir/.gitkeep" ]; then
            report_error "Stub directory $dir missing .gitkeep"
        else
            report_success "Stub directory $dir has .gitkeep"
        fi
    fi
done

# Check for transcript files
echo ""
echo "Checking for transcript files..."
transcript_files=$(find . -maxdepth 1 -name "*.txt" -type f ! -name "LICENSE" ! -name "NOTICE" 2>/dev/null || true)
if [ -n "$transcript_files" ]; then
    report_error "Transcript files found: $transcript_files"
else
    report_success "No transcript files found"
fi

# Check for large files
echo ""
echo "Checking for large files..."
large_files=$(find . -type f -not -path "./.venv/*" -not -path "./.git/*" -not -path "./htmlcov/*" -size +${MAX_SIZE_KB}k 2>/dev/null || true)
if [ -n "$large_files" ]; then
    report_error "Large files found (>${MAX_SIZE_KB}KB): $large_files"
else
    report_success "No large files found"
fi

# Check for Python cache in project directories
echo ""
echo "Checking for Python cache in project directories..."
pycache_dirs=$(find . -type d -name "__pycache__" -not -path "./.venv/*" 2>/dev/null || true)
if [ -n "$pycache_dirs" ]; then
    report_warning "Python cache directories found in project: $pycache_dirs"
else
    report_success "No Python cache in project directories"
fi

# Check for security patterns
echo ""
echo "Checking for forbidden patterns (3PAA-SHADOW containment)..."
forbidden_domains=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
    ! -path "./.venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
    ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" -exec grep -lE "$FORBIDDEN_DOMAINS" {} \; 2>/dev/null || true)
if [ -n "$forbidden_domains" ]; then
    report_error "Forbidden domains detected"
else
    report_success "No forbidden domains found"
fi

forbidden_tokens=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
    ! -path "./.venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
    ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" -exec grep -lE "$FORBIDDEN_TOKENS" {} \; 2>/dev/null || true)
if [ -n "$forbidden_tokens" ]; then
    report_error "Forbidden tokens detected"
else
    report_success "No forbidden tokens found"
fi

# Check for potential secrets
echo ""
echo "Checking for potential secrets..."
suspicious_files=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
    ! -path "./.venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
    ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" -exec grep -lE "password\s*=\s*['\"]|api[_-]?key\s*=\s*['\"]|secret\s*=\s*['\"]|token\s*=\s*['\"]|credential\s*=\s*['\"]" {} \; 2>/dev/null || true)
if [ -n "$suspicious_files" ]; then
    report_warning "Potential secrets found in: $suspicious_files"
else
    report_success "No potential secrets found"
fi

# Check git configuration
echo ""
echo "Checking git configuration..."
if git config user.name > /dev/null 2>&1; then
    git_user=$(git config user.name)
    report_success "Git user configured: $git_user"
else
    report_warning "Git user not configured locally"
fi

# Check Python environment
echo ""
echo "Checking Python environment..."
if [ -d ".venv" ]; then
    report_success "Virtual environment exists (.venv)"
    if command -v uv &> /dev/null; then
        report_success "uv package manager available"
    else
        report_error "uv package manager not found"
    fi
else
    report_warning "Virtual environment not found (.venv)"
fi

# Check for documentation organization
echo ""
echo "Checking documentation organization..."
if [ -d "docs" ]; then
    report_success "docs/ directory exists"
    if [ -f ".github/SECURITY.md" ]; then
        report_success "Security documentation present in .github/"
    else
        report_warning "Security documentation not found in .github/"
    fi
else
    report_error "docs/ directory not found"
fi

# Summary
echo ""
echo "=========================="
echo -e "${BLUE}Validation Summary${NC}"
echo "=========================="
echo -e "Errors: ${RED}${errors}${NC}"
echo -e "Warnings: ${YELLOW}${warnings}${NC}"
if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "Success checks: ${GREEN}All checks passed${NC}"
else
    echo -e "Success checks: ${RED}Some checks failed${NC}"
fi

if [ $errors -gt 0 ]; then
    echo ""
    echo -e "${RED}Validation failed with $errors error(s)${NC}"
    exit 1
elif [ $warnings -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Validation completed with $warnings warning(s)${NC}"
    exit 0
else
    echo ""
    echo -e "${GREEN}All validation checks passed!${NC}"
    exit 0
fi