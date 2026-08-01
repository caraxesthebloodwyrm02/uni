"""Pytest configuration for mangrove tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
PLATFORM_DIR = ROOT_DIR / "platform"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(PLATFORM_DIR) not in sys.path:
    sys.path.append(str(PLATFORM_DIR))


