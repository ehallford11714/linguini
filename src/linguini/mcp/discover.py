"""MCP discovery — offline fixture catalog in v0.1; live registry later."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from linguini.forge.purpose import ForgePurpose


def _load_catalog() -> dict[str, Any]:
    try:
        ref = resources.files("linguini.mcp").joinpath("catalog_fixture.json")
        return json.loads(ref.read_text(encoding="utf-8"))
    except Exception:
        here = Path(__file__).with_name("catalog_fixture.json")
        return json.loads(here.read_text(encoding="utf-8"))


def discover_for_purpose(purpose: ForgePurpose | str, *, limit: int = 10) -> list[dict[str, Any]]:
    need = purpose.need if isinstance(purpose, ForgePurpose) else str(purpose)
    tokens = {t for t in need.lower().replace("/", " ").split() if len(t) > 2}
    catalog = _load_catalog()
    scored: list[tuple[int, dict[str, Any]]] = []
    for srv in catalog.get("servers") or []:
        tags = set(srv.get("purpose_tags") or [])
        blob = f"{srv.get('id')} {srv.get('description')} {' '.join(tags)}".lower()
        score = sum(1 for t in tokens if t in blob) + sum(2 for t in tags if t in tokens)
        if "ground" in need.lower() and "grounding" in tags:
            score += 3
        if "chain" in need.lower() or "mcp" in need.lower():
            score += 1
        scored.append((score, srv))
    scored.sort(key=lambda x: (-x[0], x[1].get("id") or ""))
    out = []
    for score, srv in scored[:limit]:
        row = dict(srv)
        row["score"] = score
        out.append(row)
    return out
