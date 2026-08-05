"""Sanitize pip/npm package names — blocks shell injection even in open mode."""

from __future__ import annotations

import re

_PIP_RE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)(\[[A-Za-z0-9,_-]+\])?(==|>=|<=|~=|!=|>|<)?([A-Za-z0-9._*]*)?$"
)
_NPM_RE = re.compile(
    r"^(@[a-z0-9-~][a-z0-9-._~]*/[a-z0-9-~][a-z0-9-._~]*|[a-z0-9-~][a-z0-9-._~]*)(@[A-Za-z0-9._+-]+)?$"
)


def pip_base_name(spec: str) -> str:
    spec = spec.strip()
    m = _PIP_RE.match(spec)
    if not m:
        raise ValueError(f"invalid pip package spec: {spec!r}")
    return m.group(1)


def validate_pip_spec(spec: str) -> str:
    spec = spec.strip()
    if not spec or any(c in spec for c in " ;|&$`\\\n\r"):
        raise ValueError(f"unsafe pip package spec: {spec!r}")
    if not _PIP_RE.match(spec):
        raise ValueError(f"invalid pip package spec: {spec!r}")
    return spec


def npm_base_name(spec: str) -> str:
    spec = validate_npm_spec(spec)
    if spec.startswith("@"):
        body = spec[1:]
        scope, rest = body.split("/", 1)
        name = rest.split("@")[0]
        return f"@{scope}/{name}"
    return spec.split("@")[0]


def validate_npm_spec(spec: str) -> str:
    spec = spec.strip()
    if not spec or any(c in spec for c in " ;|&$`\\\n\r"):
        raise ValueError(f"unsafe npm package spec: {spec!r}")
    if not _NPM_RE.match(spec):
        raise ValueError(f"invalid npm package spec: {spec!r}")
    return spec
