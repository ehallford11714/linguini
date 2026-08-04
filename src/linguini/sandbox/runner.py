"""Static scan + restricted execution helpers."""

from __future__ import annotations

import ast
import re
from typing import Any, Callable

from linguini.sandbox.policy import BANNED_NAME_FRAGMENTS, SandboxPolicy


class SandboxViolation(RuntimeError):
    pass


_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([\w.]+)", re.M)


def static_scan(source: str, policy: SandboxPolicy | None = None) -> list[str]:
    """Return list of violation messages (empty if clean)."""
    policy = policy or SandboxPolicy()
    violations: list[str] = []
    lower = source.lower()
    for frag in BANNED_NAME_FRAGMENTS:
        if frag in lower and not policy.allow_network and frag in {
            "socket",
            "requests",
            "urllib",
            "http.client",
        }:
            violations.append(f"banned fragment: {frag}")
        elif frag in lower and frag in {"subprocess", "os.system", "ctypes", "importlib"}:
            violations.append(f"banned fragment: {frag}")

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"syntax error: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not policy.import_allowed(alias.name):
                    violations.append(f"disallowed import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod and not policy.import_allowed(mod):
                violations.append(f"disallowed import: {mod}")
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "os" and node.attr == "system":
                violations.append("banned call: os.system")

    for m in _IMPORT_RE.finditer(source):
        name = m.group(1)
        if not policy.import_allowed(name):
            msg = f"disallowed import: {name}"
            if msg not in violations:
                violations.append(msg)
    return violations


def run_native_callable(fn: Callable[..., Any], args: dict[str, Any] | None = None) -> Any:
    """Run a trusted in-process callable (library tools only — not raw exec)."""
    args = args or {}
    return fn(**args)
