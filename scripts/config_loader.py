#!/usr/bin/env python3
# ==============================================================================
# Script Name: config_loader.py
# Description: Configuration loader utility for Python scripts to read settings from hooks.json
# Usage: Import load_config or get_setting from scripts.config_loader
# Scope/Safety: Safe / Read-only
# Dependencies: Python 3.13+
# ==============================================================================
"""Configuration loader for Python scripts."""

import json
import sys
from pathlib import Path


def load_config() -> dict:
    """Load configuration from .devin/hooks.json."""
    repo_root = Path(__file__).resolve().parent.parent
    config_path = repo_root / ".devin" / "hooks.json"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}", file=sys.stderr)
    return {}


def get_setting(keys: list[str], default=None):
    """Retrieve nested configuration setting or return default."""
    config = load_config()
    val = config
    for key in keys:
        if isinstance(val, dict) and key in val:
            val = val[key]
        else:
            return default
    return val
