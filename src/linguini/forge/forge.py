"""ToolForge — create native novel tools; persist only on green tests."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from linguini.forge.persist import persist_native
from linguini.forge.purpose import ForgePurpose, IOExample
from linguini.forge.testloop import TestLoopResult, run_test_loop
from linguini.sandbox.policy import SandboxPolicy


@dataclass
class ForgeResult:
    ok: bool
    persisted: bool
    tool_name: str
    entry: Optional[dict[str, Any]] = None
    loop: Optional[TestLoopResult] = None
    reason: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    native_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "persisted": self.persisted,
            "tool_name": self.tool_name,
            "native_name": self.native_name or f"native.{self.tool_name}",
            "entry": self.entry,
            "loop": self.loop.to_dict() if self.loop else None,
            "reason": self.reason,
            "evidence": list(self.evidence),
        }


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower()).strip("_")
    return s or "native_op"


def forge_tool(
    purpose: ForgePurpose,
    *,
    root: Path | str,
    tool_name: str | None = None,
    max_repairs: int = 3,
    policy: SandboxPolicy | None = None,
    persist: bool = True,
    initial_source: str | None = None,
    evidence: list[dict[str, Any]] | None = None,
    chain_steps: Sequence[str] | None = None,
) -> ForgeResult:
    name = _slug(tool_name or purpose.name or "forged_op")
    loop = run_test_loop(
        purpose,
        tool_name=name,
        max_repairs=max_repairs,
        policy=policy,
        initial_source=initial_source,
        chain_steps=chain_steps,
    )
    if not loop.ok:
        return ForgeResult(
            ok=False,
            persisted=False,
            tool_name=name,
            native_name=f"native.{name}",
            loop=loop,
            reason="unit-test loop failed; nothing persisted",
            evidence=list(evidence or []),
        )
    if not persist:
        return ForgeResult(
            ok=True,
            persisted=False,
            tool_name=name,
            native_name=f"native.{name}",
            loop=loop,
            reason="tests passed; persist=False",
            evidence=list(evidence or []),
        )
    entry = persist_native(
        root,
        tool_name=name,
        source=loop.source,
        test_source=loop.test_source,
        purpose=purpose,
    )
    return ForgeResult(
        ok=True,
        persisted=True,
        tool_name=name,
        native_name=f"native.{name}",
        entry=entry,
        loop=loop,
        reason="persisted after green tests",
        evidence=list(evidence or []),
    )


def create_native_tool(
    need: str,
    *,
    root: Path | str,
    name: str,
    examples: list[IOExample] | None = None,
    invariants: list[str] | None = None,
    must_compose: Sequence[str] | None = None,
    template: str = "auto",
    persist: bool = True,
    max_repairs: int = 3,
    policy: SandboxPolicy | None = None,
) -> ForgeResult:
    """
    Always attempt to create a *new* native tool (require_native=True).

    This is the primary API for 'Linguini can create native new tools'.
    """
    ex = list(examples or [])
    inv = list(invariants or [])
    if not ex:
        ex = [
            IOExample(
                input="Acme Corp grew 12%. Demand looks fine.",
                expected={"novel": True},
            )
        ]
    if not inv:
        inv = ["output tokens are lowercase"]
    purpose = ForgePurpose(
        need=need,
        name=name,
        examples=ex,
        invariants=inv,
        must_compose=list(must_compose) if must_compose else None,
        require_native=True,
        template=template,
    )
    return forge_tool(
        purpose,
        root=root,
        tool_name=name,
        persist=persist,
        max_repairs=max_repairs,
        policy=policy,
        chain_steps=must_compose,
        evidence=[{"type": "create_native_tool", "need": need, "name": name}],
    )


def wrap_chain_as_native(
    steps: Sequence[str],
    *,
    root: Path | str,
    name: str,
    need: str | None = None,
    persist: bool = True,
    policy: SandboxPolicy | None = None,
) -> ForgeResult:
    """Persist a multi-step NLP chain as a single reusable native tool."""
    purpose = ForgePurpose(
        need=need or f"chain wrapper for {', '.join(steps)}",
        name=name,
        examples=[IOExample(input="Hello World from Acme", expected={"novel": True})],
        must_compose=list(steps),
        require_native=True,
        template="chain_wrap",
    )
    return forge_tool(
        purpose,
        root=root,
        tool_name=name,
        persist=persist,
        policy=policy,
        chain_steps=steps,
        evidence=[{"type": "wrap_chain", "steps": list(steps)}],
    )
