"""ToolForge entry — only after lean-back gap; persist only on green tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from linguini.forge.persist import persist_native
from linguini.forge.purpose import ForgePurpose
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "persisted": self.persisted,
            "tool_name": self.tool_name,
            "entry": self.entry,
            "loop": self.loop.to_dict() if self.loop else None,
            "reason": self.reason,
            "evidence": list(self.evidence),
        }


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
) -> ForgeResult:
    name = tool_name or purpose.name or "forged_op"
    name = name.removeprefix("native.")
    loop = run_test_loop(
        purpose,
        tool_name=name,
        max_repairs=max_repairs,
        policy=policy,
        initial_source=initial_source,
    )
    if not loop.ok:
        return ForgeResult(
            ok=False,
            persisted=False,
            tool_name=name,
            loop=loop,
            reason="unit-test loop failed; nothing persisted",
            evidence=list(evidence or []),
        )
    if not persist:
        return ForgeResult(
            ok=True,
            persisted=False,
            tool_name=name,
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
        entry=entry,
        loop=loop,
        reason="persisted after green tests",
        evidence=list(evidence or []),
    )
