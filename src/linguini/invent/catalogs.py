"""Load skills + allowlisted pip/npm catalogs."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from linguini.invent.pkg_names import npm_base_name, pip_base_name


def _pkg_dir(*parts: str) -> Path:
    try:
        base = resources.files("linguini.invent")
        cur: Any = base
        for p in parts:
            cur = cur.joinpath(p)
        return Path(str(cur))
    except Exception:
        return Path(__file__).resolve().parent.joinpath(*parts)


def load_lib_catalog() -> dict[str, Any]:
    path = _pkg_dir("lib_catalog.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_npm_catalog() -> dict[str, Any]:
    path = _pkg_dir("npm_catalog.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def list_libs() -> list[dict[str, Any]]:
    return list((load_lib_catalog().get("packages") or []))


def list_npm() -> list[dict[str, Any]]:
    return list((load_npm_catalog().get("packages") or []))


def lib_by_name(name: str) -> dict[str, Any] | None:
    try:
        base = pip_base_name(name)
    except ValueError:
        base = name
    for pkg in list_libs():
        if pkg.get("name") == base or base in (pkg.get("import_roots") or []):
            return pkg
    return None


def npm_by_name(name: str) -> dict[str, Any] | None:
    try:
        base = npm_base_name(name)
    except ValueError:
        base = name
    for pkg in list_npm():
        if pkg.get("name") == base:
            return pkg
    return None


def is_pip_allowlisted(name: str) -> bool:
    return lib_by_name(name) is not None


def is_npm_allowlisted(name: str) -> bool:
    return npm_by_name(name) is not None


def load_skills() -> list[dict[str, Any]]:
    skills_dir = _pkg_dir("skills")
    out: list[dict[str, Any]] = []
    if not skills_dir.is_dir():
        return out
    for path in sorted(skills_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data["_path"] = str(path)
        out.append(data)
    return out


def skill_by_id(skill_id: str) -> dict[str, Any] | None:
    for s in load_skills():
        if s.get("id") == skill_id:
            return s
    return None


def list_skills() -> list[dict[str, Any]]:
    rows = []
    for s in load_skills():
        rows.append(
            {
                "id": s.get("id"),
                "description": s.get("description"),
                "purpose_tags": list(s.get("purpose_tags") or []),
                "pip_deps": list(s.get("pip_deps") or []),
                "npm_deps": list(s.get("npm_deps") or []),
                "mcp_tools": list(s.get("mcp_tools") or []),
                "template": s.get("template"),
            }
        )
    return rows
