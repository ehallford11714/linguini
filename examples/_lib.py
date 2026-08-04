"""Shared helpers for example scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
WORKSPACE = Path(__file__).resolve().parent / "_workspace"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def workspace() -> Path:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    return WORKSPACE


def dump(label: str, obj: object) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(obj, indent=2, default=str))
