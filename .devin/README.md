# Workspace Automation and Hooks

This directory contains configuration for workspace automation, hooks, and validation in the Mangrove repository.

## Configuration Files

### `hooks.json`
- **Purpose**: Central configuration for workspace automation and hooks
- **Components**:
  - Pre-commit checks configuration
  - Pre-push checks configuration
  - Environment settings
  - Security constraints
  - Workspace validation rules

## Automated Hooks

### Pre-Commit Checks
1. **Forbidden Patterns Check** - Prevents 3PAA-SHADOW containment violations
2. **Security Linting** - Ruff security checks
3. **Code Formatting** - Ruff formatting
4. **Secret Detection** - Prevents credential commits
5. **Large File Check** - Prevents large file commits

### Pre-Push Checks
1. **Test Suite** - Runs pytest before push
2. **Workspace Audit** - Validates workspace structure

## CI/CD Integration

### GitHub Actions Integration
- **workspace-validation**: Runs workspace structure validation
- **security-scan**: Enhanced with custom script checks
- **dependency-gate**: Includes workspace validation as dependency

### Automation Layer
- All checks are integrated into CI pipeline
- Workspace validation runs before all other checks
- Security checks are enforced at multiple levels

## Best Practices

### Environment Configuration
- Python 3.13 required
- uv package manager
- Virtual environment in `.venv/`
- Max file size: 500KB for code files

### Security Constraints
- Forbidden domains: factory.ai, cursor.com, cursor.sh, workos.com
- Forbidden tokens: WorkOS, Factory
- Secret detection enabled
- 3PAA-SHADOW containment enforced

### Workspace Validation
- Stub directories must have `.gitkeep` files
- No transcript files allowed
- Documentation organized in `docs/`
- No Python cache in project directories

## Usage

### Local Development
```bash
# Run workspace validation
bash scripts/validate-workspace.sh

# Run individual checks
bash scripts/check-forbidden-patterns.sh
bash scripts/check-secrets.sh
bash scripts/check-large-files.sh
```

### Pre-Commit (if installed)
```bash
# Install pre-commit
pip install pre-commit

# Run hooks
pre-commit run --all-files
```

### CI/CD
Automatically runs on:
- Push to main/master branches
- Pull requests
- Runs in order: workspace-validation → security-scan → quality → test → dependency-gate

## Compliance

### Governance Rules
- **3PAA-SHADOW Containment**: Enforced via forbidden pattern checks
- **Trust Contract (TUV-001)**: Workspace structure compliance
- **SUSS Path Denial**: Git hooks prevent prohibited operations
- **Code Preservation**: Dual approval for infrastructure changes

### Audit Trail
All operations are logged in `.compliance-hand-off/.audit.log` for canonical hand-off verification.

## Maintenance

### Updating Configuration
- Modify `.devin/hooks.json` for general settings
- Update individual check scripts for specific logic
- Adjust CI workflow for pipeline changes
- Update CODEOWNERS for approval requirements

### Adding New Checks
1. Create script in `scripts/` directory
2. Add to `.pre-commit-config.yaml`
3. Add to CI workflow if needed
4. Update CODEOWNERS for proper review
5. Document in this README