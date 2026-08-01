# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please send an email to the repository maintainers privately. We will work with you to assess the risk and coordinate a fix before public disclosure.

### Security Contact

- **Email**: [Maintainer's security contact]
- **PGP Key**: [Optional: Provide PGP key for encrypted communication]

## Security Policy Scope

This security policy applies to:
- All code in the mangrove repository
- All dependencies and third-party libraries
- CI/CD pipelines and infrastructure
- Documentation and configuration files

## Baseline Security Rules

### 1. Code Quality Gates
- All code must pass linting checks (ruff) before merge
- All tests must pass with minimum coverage thresholds
- No security vulnerabilities in dependencies above medium severity

### 2. Dependency Management
- Dependencies are updated monthly via Dependabot
- All dependency changes require review and testing
- Vulnerability patches are prioritized and expedited

### 3. Access Control
- Repository maintains branch protection rules requiring:
  - At least 1 approving review for code changes
  - All CI checks must pass
  - Admin enforcement enabled
- Code owners must approve changes to critical paths

### 4. Forbidden Domains and Services
Per governance rules (3PAA-SHADOW containment):
- **Hard Deny**: `factory.ai`, `cursor.com`, `cursor.sh`, `workos.com`
- **Forbidden Tokens**: `WorkOS`, `Factory`
- **Blocked Ports**: 54621, 8081, 40925 (8788 allowed only for x-change production)

### 5. Code Preservation Rules
- No deletion of core infrastructure without explicit approval
- Breaking changes require migration path and documentation
- All tests must be updated to reflect structural changes
- Configuration changes must be backwards compatible

## Threat Model

### Primary Threats
1. **Supply Chain Attacks**: Malicious dependencies or compromised packages
2. **Code Injection**: Unauthorized code changes or commits
3. **Credential Leakage**: Exposure of secrets or API keys
4. **Dependency Confusion**: Typosquatting or package hijacking

### Mitigation Strategies
- Pin exact dependency versions where possible
- Require code review for all changes
- Use secrets management (never commit credentials)
- Verify package signatures when available
- Monitor for suspicious activity

## Security Best Practices

### For Contributors
1. Never commit secrets, API keys, or sensitive data
2. Follow the established code review process
3. Keep dependencies updated and review changelogs
4. Report security concerns through private channels
5. Use two-factor authentication for GitHub accounts

### For Maintainers
1. Review all dependency updates for security implications
2. Monitor security advisories for dependencies
3. Maintain and test incident response procedures
4. Keep documentation current with security practices
5. Regular security audits of code and infrastructure

## Incident Response

### Severity Levels
- **Critical**: Immediate risk to users or data (within 24 hours)
- **High**: Significant security impact (within 72 hours)
- **Medium**: Limited security impact (within 1 week)
- **Low**: Minor security issues (next release)

### Response Process
1. **Discovery**: Vulnerability reported or discovered
2. **Assessment**: Evaluate severity and impact
3. **Coordination**: Plan fix and disclosure timeline
4. **Remediation**: Develop and test security patch
5. **Disclosure**: Public disclosure with security advisory
6. **Post-Mortem**: Document lessons learned

## Compliance Notes

This repository adheres to the Mangrove ecosystem governance rules:
- Trust Contract (TUV-001) compliance
- 3PAA-SHADOW containment mandate
- SUSS path denial enforcement
- Git hooks prevent prohibited operations

## Security Updates

Security updates will be:
- Released as soon as feasible after assessment
- Clearly marked in release notes
- Coordinated with affected users when possible
- Include upgrade instructions and migration guides

## Additional Resources

- [GitHub Security Advisories](https://github.com/caraxesthebloodwyrm02/uni/security/advisories)
- [Dependabot Alerts](https://github.com/caraxesthebloodwyrm02/uni/security/dependabot)
- [CodeQL Analysis](https://github.com/caraxesthebloodwyrm02/uni/security/code-scanning)

## License

This project is licensed under the MIT License. See LICENSE file for details.
