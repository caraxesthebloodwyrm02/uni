# Security Guide for Mangrove Repository

## Overview

This guide provides comprehensive security practices and procedures for the Mangrove repository. All contributors and maintainers must follow these guidelines to ensure the security and integrity of the codebase.

## Core Security Principles

### 1. Zero Trust Architecture
- Verify all inputs, dependencies, and external data
- Assume all systems may be compromised
- Implement defense in depth across all layers

### 2. Least Privilege
- Grant minimum necessary permissions for any operation
- Use scoped access tokens instead of full credentials
- Regularly audit and review access permissions

### 3. Defense in Depth
- Multiple layers of security controls
- Fail-safe defaults
- Redundant security measures

## Code Security Practices

### Secret Management
**ABSOLUTE RULES:**
- **NEVER** commit secrets, API keys, or credentials to the repository
- **NEVER** include secrets in configuration files
- **NEVER** log sensitive information

**Allowed Practices:**
- Use environment variables for runtime configuration
- Use GitHub Secrets for CI/CD workflows
- Use proper secret management services (e.g., HashiCorp Vault)

**Detection:**
- Repository has pre-commit hooks to detect common secret patterns
- CI pipeline scans for potential secrets
- Manual review of all changes

### Dependency Security

**Dependency Addition Process:**
1. Research the package security history
2. Check for known vulnerabilities (CVE database)
3. Review maintainers and project activity
4. Verify package signature if available
5. Test thoroughly in isolated environment
6. Document security considerations

**Dependency Updates:**
- Dependabot handles automated updates
- Security patches prioritized over feature updates
- Major version updates require manual review
- All dependency changes require maintainer approval

**Prohibited Dependencies:**
- Packages from blocked domains (factory.ai, cursor.com, cursor.sh, workos.com)
- Packages with security advisories above medium severity
- Unmaintained or abandoned packages

### Code Review Security Checklist

**Before Approving:**
- [ ] No secrets or sensitive data included
- [ ] No hardcoded credentials or keys
- [ ] Proper input validation and sanitization
- [ ] No SQL injection or XSS vulnerabilities
- [ ] Proper error handling without information leakage
- [ ] Dependencies reviewed and justified
- [ ] Tests cover security-critical paths
- [ ] No known vulnerabilities in new dependencies

## Configuration Security

### File Permissions
- Configuration files should be mode 644 (rw-r--r--)
- Executable scripts should be mode 755 (rwxr-xr-x)
- Sensitive configuration should use environment variables

### Environment Variables
- Never commit `.env` files
- Use `.env.example` as template
- Document required environment variables
- Use secrets management for production

### Network Security
- Use HTTPS for all external communications
- Validate SSL/TLS certificates
- Implement proper timeout handling
- Rate limit external API calls

## CI/CD Security

### Workflow Security
- All workflows must be reviewed
- Use pinned action versions (no @latest)
- Minimal permissions for GitHub tokens
- Audit log of all workflow runs

### Artifact Security
- Scan artifacts for vulnerabilities
- Sign artifacts when possible
- Verify artifact integrity
- Clean up old artifacts regularly

### Deployment Security
- Separate environments for dev/staging/prod
- Use different credentials per environment
- Implement blue-green deployments
- Rollback procedures tested

## Governance Compliance

### 3PAA-SHADOW Containment
**Hard Deny List:**
- `factory.ai` - Prohibited domain
- `cursor.com` - Prohibited domain  
- `cursor.sh` - Prohibited domain
- `workos.com` - Prohibited domain

**Blocked Ports:**
- 54621 - Blocked for all uses
- 8081 - Blocked for all uses
- 40925 - Blocked for all uses
- 8788 - Blocked except for x-change production (local bind only)

**Forbidden Tokens:**
- `WorkOS` - Forbidden in code and documentation
- `Factory` - Forbidden in code and documentation

### SUSS Path Denial
- Git hooks prevent commits with SUSS paths
- `.gitignore` prevents tracking SUSS files
- Override requires `GIT_ALLOW_SUSS=1` (audit trail written)

### Trust Contract (TUV-001)
- Follow canonical rules from `/home/irfankabir/docs/AGENTS.md`
- Adhere to established development contracts
- Maintain audit trails for critical operations

## Incident Response

### Security Incident Categories

**P0 - Critical (Immediate)**
- Production system compromise
- Data breach or unauthorized access
- Complete system unavailability

**P1 - High (Within 24 hours)**
- Security vulnerability in production
- Suspicious activity detected
- Dependency vulnerability > medium severity

**P2 - Medium (Within 1 week)**
- Security vulnerability in non-production
- Compliance violations
- Policy violations

**P3 - Low (Next release)**
- Minor security issues
- Documentation gaps
- Best practice improvements

### Response Procedure

1. **Detection**
   - Monitor security alerts
   - Review dependency advisories
   - Audit access logs

2. **Assessment**
   - Determine severity level
   - Assess impact and scope
   - Identify affected systems

3. **Containment**
   - Isolate affected systems
   - Prevent further damage
   - Preserve evidence

4. **Remediation**
   - Develop security patch
   - Test in isolated environment
   - Deploy to production

5. **Recovery**
   - Monitor for recurrence
   - Update documentation
   - Improve processes

6. **Post-Mortem**
   - Document timeline
   - Identify root causes
   - Implement improvements

## Security Testing

### Automated Security Checks
- Dependency vulnerability scanning (Dependabot)
- Static analysis (ruff security rules)
- Secret detection (pre-commit hooks)
- CodeQL analysis (if enabled)

### Manual Security Testing
- Penetration testing (quarterly)
- Security code reviews (monthly)
- Configuration audits (monthly)
- Access reviews (quarterly)

### Security Metrics
- Vulnerability remediation time
- Security test coverage
- Security incident frequency
- Compliance score

## Training and Awareness

### Required Training
- Security fundamentals (annual)
- Threat modeling (annual)
- Incident response (annual)
- Tool-specific training (as needed)

### Security Communications
- Security announcements via email
- Weekly security digest
- Monthly security meeting
- Incident response alerts

## Contacts and Resources

### Security Team
- **Primary**: caraxesthebloodwyrm02
- **Secondary**: irfankabir02
- **Emergency**: [Add emergency contact if applicable]

### External Resources
- [GitHub Security Documentation](https://docs.github.com/en/security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)

### Internal Resources
- [.github/SECURITY.md](.github/SECURITY.md) - Security policy
- [CLAUDE.md](CLAUDE.md) - Governance and safety rules
- [.github/CODEOWNERS](.github/CODEOWNERS) - Code ownership

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-08-01 | 1.0 | Initial security guide | System |

---

**Last Updated**: 2026-08-01
**Next Review**: 2026-11-01 (quarterly review)
**Owner**: caraxesthebloodwyrm02