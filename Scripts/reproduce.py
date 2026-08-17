#!/usr/bin/env python3
"""Run the complete deterministic evaluation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causalcred_eval.cli import reproduce  # noqa: E402


if __name__ == "__main__":
    reproduce(ROOT)
