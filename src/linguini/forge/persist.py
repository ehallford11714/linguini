"""Persist natives only after green tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from linguini.forge.purpose import ForgePurpose


def persist_native(
    root: Path | str,
    *,
    tool_name: str,
    source: str,
    test_source: str,
    purpose: ForgePurpose,
    description: str = "",
) -> dict[str, Any]:
    root = Path(root)
    native_dir = root / ".linguini" / "native_tools"
    native_dir.mkdir(parents=True, exist_ok=True)
    slug = tool_name.removeprefix("native.")
    mod_path = native_dir / f"{slug}.py"
    test_path = native_dir / f"test_{slug}.py"
    mod_path.write_text(source, encoding="utf-8")
    # Rewrite test module path to sibling tool file
    fixed_tests = test_source.replace("TOOL_MODULE.py", f"{slug}.py")
    test_path.write_text(fixed_tests, encoding="utf-8")

    reg_path = native_dir / "registry.yaml"
    data: dict[str, Any] = {"tools": []}
    if reg_path.exists():
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8")) or {"tools": []}
        data.setdefault("tools", [])

    entry = {
        "name": slug,
        "description": description or purpose.need,
        "path": str(mod_path.relative_to(root)).replace("\\", "/"),
        "tests_path": str(test_path.relative_to(root)).replace("\\", "/"),
        "purpose_hash": purpose.purpose_hash(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }
    tools = [t for t in data["tools"] if t.get("name") != slug]
    tools.append(entry)
    data["tools"] = tools
    reg_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return entry
