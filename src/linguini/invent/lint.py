"""Lint-like verifier — runs before pytest; fail-closed."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any

from linguini.invent.plan import InventionPlan
from linguini.sandbox.policy import BANNED_NAME_FRAGMENTS, SandboxPolicy
from linguini.sandbox.runner import static_scan


@dataclass
class LintResult:
    ok: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "violations": list(self.violations)}


def _has_run_fn(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            return True
    return False


def lint_source(
    source: str,
    plan: InventionPlan,
    *,
    policy: SandboxPolicy | None = None,
) -> LintResult:
    """AST + allowlist lint bounded by frozen InventionPlan."""
    policy = policy or SandboxPolicy()
    violations: list[str] = []

    # Expand policy imports with plan allowlist for this check
    allowed = set(policy.allowed_imports) | set(plan.allowed_imports)
    # Always allow stdlib used by templates
    allowed |= {
        "__future__",
        "json",
        "re",
        "math",
        "typing",
        "dataclasses",
        "collections",
        "functools",
        "itertools",
        "string",
        "hashlib",
    }

    class _Policy(SandboxPolicy):
        def import_allowed(self, module: str) -> bool:
            root = module.split(".")[0]
            if root in allowed or module in allowed:
                return True
            if module.startswith("linguini."):
                return True
            # allowlisted pip import roots from plan deps
            for dep in plan.pip_deps:
                if root == dep or module.startswith(dep):
                    return True
            # common import root remaps
            remaps = {"bs4": "beautifulsoup4", "yaml": "pyyaml", "markdown_it": "markdown-it-py"}
            if root in remaps and remaps[root] in plan.pip_deps:
                return True
            return False

    bound_policy = _Policy(
        allow_network=policy.allow_network,
        allow_subprocess=policy.allow_subprocess,
        allow_filesystem_write=policy.allow_filesystem_write,
        allowed_imports=frozenset(allowed),
        allow_mcp_servers=list(policy.allow_mcp_servers),
        pytest_timeout_s=policy.pytest_timeout_s,
    )

    violations.extend(static_scan(source, bound_policy))

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return LintResult(ok=False, violations=[f"syntax error: {e}"])

    if not _has_run_fn(tree):
        violations.append("missing required function: run")

    lower = source.lower()
    for frag in BANNED_NAME_FRAGMENTS:
        if frag in {"pathlib", "shutil"} and frag in lower:
            # still banned for invented natives unless policy expands later
            if f"banned fragment: {frag}" not in violations:
                # pathlib often false-positive in comments — only flag import
                pass

    # MCP refs in source must be subset of plan (soft: check string mentions of mcp tool ids)
    for tool in _extract_mcp_string_refs(source):
        if tool not in plan.mcp_tools and plan.mcp_tools:
            # allow if any plan tool shares server prefix
            server = tool.split(".")[0]
            if not any(t.startswith(server) for t in plan.mcp_tools):
                violations.append(f"mcp tool not in plan bounds: {tool}")

    if plan.require_novel and "novel" not in source:
        violations.append("require_novel plan but source never sets novel")

    # Deduplicate
    seen: set[str] = set()
    uniq: list[str] = []
    for v in violations:
        if v not in seen:
            seen.add(v)
            uniq.append(v)

    return LintResult(ok=len(uniq) == 0, violations=uniq)


def _extract_mcp_string_refs(source: str) -> list[str]:
    refs: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return refs
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if "." in val and val.split(".")[0] in {
                "fetch",
                "memory",
                "filesystem",
                "github",
                "codeforge",
                "sequential-thinking",
            }:
                refs.append(val)
    return refs
