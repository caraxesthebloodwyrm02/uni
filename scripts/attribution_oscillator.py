#!/usr/bin/env python3
# ==============================================================================
# Script Name: attribution_oscillator.py
# Description: Generate and append checksum of runtime and binaries to compliance log on git checkout/session boundary
# Scope/Safety: Safe / Writes to compliance audit log
# Dependencies: Python 3.13+
# ==============================================================================
"""
Attribution Chain: SHA256 digest of the runtime, environment, and binary
state at git checkout / session boundaries. Writes the digest to
`.compliance-hand-off/.audit.log` as literal evidence; no verification claim
is made.

The chain is literal: a checksum and a heads-pointer. Nothing more.
"""

import argparse
import datetime
import getpass
import hashlib
import socket
import sys
from pathlib import Path

from scripts.config_loader import get_setting

# The core binaries / structural definitions to track
CORE_BINARIES = [
    "uv.lock",
    "pyproject.toml",
    "mangrove_platform/apparat/sisa.py",
]


def sha256_file(path: Path) -> str:
    """Return SHA256 hex digest of a file, or 'MISSING'."""
    if not path.exists():
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Attribution Chain")
    parser.add_argument("--prev-head", default="HEAD@{1}", help="Previous commit hash")
    parser.add_argument("--new-head", default="HEAD", help="New commit hash")
    args = parser.parse_args()

    # Runtime
    runtime_ts = datetime.datetime.now(datetime.UTC).isoformat()

    # Environment
    env_user = getpass.getuser()
    env_host = socket.gethostname()
    env_py = sys.version.split(" ")[0]
    environment_cog = f"{env_user}@{env_host}|py-{env_py}"

    # Binary
    repo_root = Path(__file__).resolve().parent.parent
    binary_cogs = {}
    for b in CORE_BINARIES:
        binary_cogs[b] = sha256_file(repo_root / b)

    binary_summary = "|".join([f"{k}:{v[:8]}" for k, v in binary_cogs.items()])

    # Payload + SHA256
    payload = (
        f"{runtime_ts}::{environment_cog}::{binary_summary}::{args.prev_head}->{args.new_head}"
    )
    digest = hashlib.sha256(payload.encode("utf-8"))
    checksum_hex = digest.hexdigest()

    # Append literal evidence to audit log
    compliance_dir = get_setting(["environment", "complianceDirectory"], ".compliance-hand-off")
    audit_log_path = repo_root / compliance_dir / ".audit.log"
    log_entry = f"{runtime_ts}  checkout-attribution  {env_user}-oscillator  sum:{checksum_hex[:12]} | heads:{args.prev_head}->{args.new_head}\n"

    try:
        # Ensure the directory exists and write to the audit log
        audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(audit_log_path, "a") as f:
            f.write(log_entry)
    except OSError as e:
        print(f"CRITICAL: Failed to write to audit log: {e}", file=sys.stderr)
        return 1

    print(f"Attribution chain recorded. Checksum: {checksum_hex[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
