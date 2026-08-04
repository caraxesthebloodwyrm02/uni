# Security Policy

## Supported Versions

This project is pre-1.0 (current: `0.2.0`). Only the latest release on
`main` receives security fixes.

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

Do **not** open a public issue for security problems.

- Report privately to the maintainer (Irfan Kabir).
- Include: affected version, a minimal reproducer, and the impact you believe
  the issue has.
- Expect an acknowledgement within 7 days and a fix or mitigation plan within
  30 days for confirmed issues.

## Security Posture

The live attack surface is the MCP server (`mangrove_platform/mcp/`). It uses:

- Pydantic input validation with a phase-name whitelist (`security.py`)
- MCP tool safety annotations on all 6 tools
- Fixed-window per-tool rate limiting
- Structured audit logging of tool invocations

Governance constraints (3PAA-SHADOW containment, forbidden tokens/domains,
SUSS path denial) are enforced by `scripts/check-forbidden-patterns.sh`,
`scripts/check-secrets.sh`, and `scripts/check-large-files.sh`.
