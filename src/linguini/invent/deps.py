"""Allowlisted pip install into isolated forge venv."""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from linguini.invent.catalogs import is_pip_allowlisted, lib_by_name


@dataclass
class DepsResult:
    ok: bool
    python: str
    installed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    venv_dir: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "python": self.python,
            "installed": list(self.installed),
            "skipped": list(self.skipped),
            "errors": list(self.errors),
            "venv_dir": self.venv_dir,
        }


def forge_venv_dir(root: Path | str) -> Path:
    return Path(root) / ".linguini" / "forge_venv"


def forge_python(root: Path | str) -> Path:
    vdir = forge_venv_dir(root)
    if os.name == "nt":
        return vdir / "Scripts" / "python.exe"
    return vdir / "bin" / "python"


def ensure_forge_venv(root: Path | str) -> Path:
    vdir = forge_venv_dir(root)
    py = forge_python(root)
    if not py.exists():
        vdir.parent.mkdir(parents=True, exist_ok=True)
        venv.create(str(vdir), with_pip=True, clear=False)
    return py


def ensure_allowlisted_deps(
    root: Path | str,
    deps: list[str],
    *,
    allow_pip_install: bool = True,
    allow_network_packages: bool = False,
) -> DepsResult:
    """Install only allowlisted packages into `.linguini/forge_venv`."""
    py = ensure_forge_venv(root)
    result = DepsResult(ok=True, python=str(py), venv_dir=str(forge_venv_dir(root)))
    if not deps:
        return result

    to_install: list[str] = []
    for dep in deps:
        if not is_pip_allowlisted(dep):
            result.ok = False
            result.errors.append(f"pip package not allowlisted: {dep}")
            continue
        info = lib_by_name(dep) or {}
        if info.get("network") and not allow_network_packages:
            result.skipped.append(dep)
            result.errors.append(f"network package blocked by policy: {dep}")
            result.ok = False
            continue
        to_install.append(dep)

    if not result.ok and not to_install:
        return result

    if not allow_pip_install:
        result.skipped.extend(to_install)
        return result

    if to_install:
        # Ensure pytest available in forge venv for testloop
        pkgs = list(dict.fromkeys(to_install + ["pytest"]))
        proc = subprocess.run(
            [str(py), "-m", "pip", "install", "--disable-pip-version-check", "-q", *pkgs],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            result.ok = False
            result.errors.append(proc.stderr[-2000:] or proc.stdout[-2000:] or "pip install failed")
        else:
            result.installed = to_install
    return result


def resolve_pytest_python(root: Path | str, *, prefer_forge: bool = True) -> str:
    if prefer_forge:
        py = forge_python(root)
        if py.exists():
            return str(py)
    return sys.executable
