"""Pip + npm installs into isolated forge environments (allowlist or open mode)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from linguini.invent.catalogs import is_npm_allowlisted, is_pip_allowlisted, lib_by_name, npm_by_name
from linguini.invent.pkg_names import npm_base_name, pip_base_name, validate_npm_spec, validate_pip_spec


@dataclass
class DepsResult:
    ok: bool
    python: str
    installed: list[str] = field(default_factory=list)
    npm_installed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    venv_dir: str = ""
    node_dir: str = ""
    open_pip: bool = False
    open_npm: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "python": self.python,
            "installed": list(self.installed),
            "npm_installed": list(self.npm_installed),
            "skipped": list(self.skipped),
            "errors": list(self.errors),
            "venv_dir": self.venv_dir,
            "node_dir": self.node_dir,
            "open_pip": self.open_pip,
            "open_npm": self.open_npm,
        }


def forge_venv_dir(root: Path | str) -> Path:
    return Path(root) / ".linguini" / "forge_venv"


def forge_node_dir(root: Path | str) -> Path:
    return Path(root) / ".linguini" / "forge_node"


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


def ensure_forge_node(root: Path | str) -> Path:
    ndir = forge_node_dir(root)
    ndir.mkdir(parents=True, exist_ok=True)
    pkg = ndir / "package.json"
    if not pkg.exists():
        pkg.write_text('{"name":"linguini-forge-node","private":true}\n', encoding="utf-8")
    return ndir


def _which_npm() -> str | None:
    return shutil.which("npm")


def _which_node() -> str | None:
    return shutil.which("node")


def ensure_pip_deps(
    root: Path | str,
    deps: list[str],
    *,
    allow_pip_install: bool = True,
    allow_open_pip: bool = False,
    allow_network_packages: bool = False,
) -> DepsResult:
    """Install pip packages into `.linguini/forge_venv` (allowlist or open)."""
    py = ensure_forge_venv(root)
    result = DepsResult(
        ok=True,
        python=str(py),
        venv_dir=str(forge_venv_dir(root)),
        node_dir=str(forge_node_dir(root)),
        open_pip=allow_open_pip,
    )
    if not deps:
        return result

    to_install: list[str] = []
    for dep in deps:
        try:
            spec = validate_pip_spec(dep)
            base = pip_base_name(spec)
        except ValueError as e:
            result.ok = False
            result.errors.append(str(e))
            continue

        listed = is_pip_allowlisted(base)
        if not listed and not allow_open_pip:
            result.ok = False
            result.errors.append(f"pip package not allowlisted (enable allow_open_pip): {base}")
            continue

        info = lib_by_name(base) or {}
        # Catalog network:true = runtime network capability (httpx etc.)
        if listed and info.get("network") and not allow_network_packages:
            result.skipped.append(spec)
            result.errors.append(f"runtime-network package blocked by policy: {base}")
            result.ok = False
            continue
        if not listed and allow_open_pip and not allow_network_packages:
            result.errors.append(f"open pip requires allow_network for: {base}")
            result.ok = False
            continue
        to_install.append(spec)

    if not to_install:
        return result

    if not allow_pip_install:
        result.skipped.extend(to_install)
        result.ok = False
        result.errors.append("allow_pip_install=False")
        return result

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


def ensure_npm_deps(
    root: Path | str,
    deps: list[str],
    *,
    allow_npm_install: bool = True,
    allow_open_npm: bool = False,
    allow_network: bool = False,
) -> DepsResult:
    """Install npm packages into `.linguini/forge_node` (allowlist or open)."""
    ndir = ensure_forge_node(root)
    result = DepsResult(
        ok=True,
        python=str(forge_python(root)) if forge_python(root).exists() else sys.executable,
        venv_dir=str(forge_venv_dir(root)),
        node_dir=str(ndir),
        open_npm=allow_open_npm,
    )
    if not deps:
        return result

    npm = _which_npm()
    if not npm:
        result.ok = False
        result.errors.append("npm not found on PATH")
        return result

    to_install: list[str] = []
    for dep in deps:
        try:
            spec = validate_npm_spec(dep)
            base = npm_base_name(spec)
        except ValueError as e:
            result.ok = False
            result.errors.append(str(e))
            continue

        listed = is_npm_allowlisted(base)
        if not listed and not allow_open_npm:
            result.ok = False
            result.errors.append(f"npm package not allowlisted (enable allow_open_npm): {base}")
            continue
        info = npm_by_name(base) or {}
        if listed and info.get("network") and not allow_network:
            result.skipped.append(spec)
            result.ok = False
            result.errors.append(f"runtime-network npm package blocked: {base}")
            continue
        if not listed and allow_open_npm and not allow_network:
            result.ok = False
            result.errors.append(f"open npm requires allow_network for: {base}")
            continue
        to_install.append(spec)

    if not to_install:
        return result

    if not allow_npm_install:
        result.skipped.extend(to_install)
        result.ok = False
        result.errors.append("allow_npm_install=False")
        return result

    proc = subprocess.run(
        [npm, "install", "--ignore-scripts", "--no-audit", "--no-fund", *to_install],
        cwd=str(ndir),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        result.ok = False
        result.errors.append(proc.stderr[-2000:] or proc.stdout[-2000:] or "npm install failed")
    else:
        result.npm_installed = to_install
    return result


def ensure_plan_deps(
    root: Path | str,
    *,
    pip_deps: list[str],
    npm_deps: list[str],
    allow_pip_install: bool = True,
    allow_npm_install: bool = True,
    allow_open_pip: bool = False,
    allow_open_npm: bool = False,
    allow_network: bool = False,
) -> DepsResult:
    """Install both ecosystems for an invention plan."""
    pip_r = ensure_pip_deps(
        root,
        pip_deps,
        allow_pip_install=allow_pip_install,
        allow_open_pip=allow_open_pip,
        allow_network_packages=allow_network,
    )
    npm_r = ensure_npm_deps(
        root,
        npm_deps,
        allow_npm_install=allow_npm_install,
        allow_open_npm=allow_open_npm,
        allow_network=allow_network,
    )
    return DepsResult(
        ok=pip_r.ok and npm_r.ok,
        python=pip_r.python,
        installed=pip_r.installed,
        npm_installed=npm_r.npm_installed,
        skipped=pip_r.skipped + npm_r.skipped,
        errors=pip_r.errors + npm_r.errors,
        venv_dir=pip_r.venv_dir,
        node_dir=npm_r.node_dir,
        open_pip=allow_open_pip,
        open_npm=allow_open_npm,
    )


# Back-compat alias
def ensure_allowlisted_deps(
    root: Path | str,
    deps: list[str],
    *,
    allow_pip_install: bool = True,
    allow_network_packages: bool = False,
    allow_open_pip: bool = False,
) -> DepsResult:
    return ensure_pip_deps(
        root,
        deps,
        allow_pip_install=allow_pip_install,
        allow_open_pip=allow_open_pip,
        allow_network_packages=allow_network_packages,
    )


def resolve_pytest_python(root: Path | str, *, prefer_forge: bool = True) -> str:
    if prefer_forge:
        py = forge_python(root)
        if py.exists():
            return str(py)
    return sys.executable


def node_available() -> bool:
    return _which_node() is not None and _which_npm() is not None
