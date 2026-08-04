"""MCP discovery — fixture catalog by default; optional local overlay (v0.2 path to live registry)."""

from __future__ import annotations

import json
import os
from importlib import resources
from pathlib import Path
from typing import Any

from linguini.forge.purpose import ForgePurpose


def _load_fixture() -> dict[str, Any]:
    try:
        ref = resources.files("linguini.mcp").joinpath("catalog_fixture.json")
        return json.loads(ref.read_text(encoding="utf-8"))
    except Exception:
        here = Path(__file__).with_name("catalog_fixture.json")
        return json.loads(here.read_text(encoding="utf-8"))


def _load_overlay() -> dict[str, Any] | None:
    """Optional local catalog JSON via LINGUINI_MCP_CATALOG (file path)."""
    path = os.environ.get("LINGUINI_MCP_CATALOG", "").strip()
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def load_catalog() -> tuple[dict[str, Any], str]:
    """Return (catalog, source) where source is fixture|overlay|merged."""
    fixture = _load_fixture()
    overlay = _load_overlay()
    if not overlay:
        return fixture, "fixture"
    servers = list(fixture.get("servers") or [])
    by_id = {s.get("id"): i for i, s in enumerate(servers)}
    for srv in overlay.get("servers") or []:
        sid = srv.get("id")
        if sid in by_id:
            servers[by_id[sid]] = srv
        else:
            servers.append(srv)
            by_id[sid] = len(servers) - 1
    return {"servers": servers}, "merged"


def discover_for_purpose(
    purpose: ForgePurpose | str,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    need = purpose.need if isinstance(purpose, ForgePurpose) else str(purpose)
    tokens = {t for t in need.lower().replace("/", " ").split() if len(t) > 2}
    catalog, source = load_catalog()
    scored: list[tuple[int, dict[str, Any]]] = []
    for srv in catalog.get("servers") or []:
        tags = set(srv.get("purpose_tags") or [])
        blob = f"{srv.get('id')} {srv.get('description')} {' '.join(tags)}".lower()
        score = sum(1 for t in tokens if t in blob) + sum(2 for t in tags if t in tokens)
        if "ground" in need.lower() and "grounding" in tags:
            score += 3
        if "chain" in need.lower() or "mcp" in need.lower():
            score += 1
        if "forge" in need.lower() or "native" in need.lower():
            if "code" in tags or "forge" in tags:
                score += 2
        scored.append((score, srv))
    scored.sort(key=lambda x: (-x[0], x[1].get("id") or ""))
    out = []
    for score, srv in scored[:limit]:
        row = dict(srv)
        row["score"] = score
        row["catalog_source"] = source
        out.append(row)
    return out
