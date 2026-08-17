#!/usr/bin/env python3
"""Verify all registered results in an existing evaluation run."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causalcred_eval.cli import verify  # noqa: E402


if __name__ == "__main__":
    verify(ROOT)
