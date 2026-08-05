"""Import only allowlisted library modules."""

from __future__ import annotations

import importlib
from typing import Any

from linguini.invent.catalogs import is_pip_allowlisted, lib_by_name


def import_allowlisted(module: str, *, package_name: str | None = None) -> Any:
    """Import a module if its package is on the lib allowlist."""
    root = module.split(".")[0]
    pkg = package_name or root
    # remap common roots
    remaps = {"bs4": "beautifulsoup4", "yaml": "pyyaml", "markdown_it": "markdown-it-py"}
    catalog_name = remaps.get(root, pkg)
    if not is_pip_allowlisted(catalog_name) and not is_pip_allowlisted(root):
        info = lib_by_name(root)
        if info is None:
            raise ImportError(f"package not on invent allowlist: {catalog_name}")
    return importlib.import_module(module)
