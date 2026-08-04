#!/usr/bin/env bash
# validate-workspace.sh - Comprehensive workspace validation
# Validates compliance with best practices, hooks, and governance rules

set -euo pipefail

# Source shared validation library
. scripts/validate-lib.sh

# Initialize configuration
init_validation ".devin/hooks.json"

echo -e "${BLUE}Workspace Validation${NC}"
echo "=========================="
# Note: BLUE header is a section banner, not a status; report_* helpers cover
# per-check status. Keep ${BLUE} here for visual structure.

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
large_files=$(find . -type f -not -path "./.venv/*" -not -path "./venv/*" -not -path "./.git/*" -not -path "./htmlcov/*" -not -path "./.mypy_cache/*" -not -path "./.opencode/*" -not -path "./.pytest_cache/*" -size +${MAX_SIZE_KB}k 2>/dev/null || true)
if [ -n "$large_files" ]; then
    report_error "Large files found (>${MAX_SIZE_KB}KB): $large_files"
else
    report_success "No large files found"
fi

# Check for Python cache in project directories
echo ""
echo "Checking for Python cache in project directories..."
pycache_dirs=$(find . -type d -name "__pycache__" -not -path "./.venv/*" -not -path "./venv/*" 2>/dev/null || true)
if [ -n "$pycache_dirs" ]; then
    report_warning "Python cache directories found in project: $pycache_dirs"
else
    report_success "No Python cache in project directories"
fi

# Check for security patterns
echo ""
echo "Checking for forbidden patterns (3PAA-SHADOW containment)..."
forbidden_domains=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
    ! -path "./.venv/*" ! -path "./venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
    ! -path "./.mypy_cache/*" ! -path "./.opencode/*" ! -path "./.pytest_cache/*" \
    ! -path "./.devin/*" ! -path "*/mangrove_platform/apparat/phase_handlers.py" -exec grep -lE "$FORBIDDEN_DOMAINS" {} \; 2>/dev/null || true)
if [ -n "$forbidden_domains" ]; then
    report_error "Forbidden domains detected"
else
    report_success "No forbidden domains found"
fi

forbidden_tokens=$(find . -type f \( -name "*.py" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
    ! -path "./.venv/*" ! -path "./venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
    ! -path "./.mypy_cache/*" ! -path "./.opencode/*" ! -path "./.pytest_cache/*" \
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
    ! -path "./.venv/*" ! -path "./venv/*" ! -path "./.git/*" ! -path "./htmlcov/*" \
    ! -path "./.mypy_cache/*" ! -path "./.opencode/*" ! -path "./.pytest_cache/*" \
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
    report_error "Validation failed with $errors error(s)"
    exit 1
elif [ $warnings -gt 0 ]; then
    report_warning "Validation completed with $warnings warning(s)"
    exit 0
else
    report_success "All validation checks passed!"
    exit 0
fi
