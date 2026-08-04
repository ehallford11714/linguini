"""Public Linguini facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from linguini.forge.forge import ForgeResult, create_native_tool, forge_tool, wrap_chain_as_native
from linguini.forge.purpose import ForgePurpose, IOExample
from linguini.ground.grounding import GroundingReport, ground_purpose
from linguini.leanback.planner import LeanBackResult, lean_back
from linguini.mcp.chain import run_chain
from linguini.mcp.discover import discover_for_purpose
from linguini.sandbox.policy import SandboxPolicy
from linguini.suite.nlp import NLPSuite
from linguini.tools.library import ToolLibrary


@dataclass
class FulfillResult:
    mode: str  # chain | forge | refused
    ok: bool
    grounding: GroundingReport
    leanback: Optional[LeanBackResult] = None
    forge: Optional[ForgeResult] = None
    discover: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ok": self.ok,
            "reason": self.reason,
            "grounding": self.grounding.to_dict(),
            "leanback": self.leanback.to_dict() if self.leanback else None,
            "forge": self.forge.to_dict() if self.forge else None,
            "discover": list(self.discover),
            "evidence": list(self.evidence),
        }


class Linguini:
    def __init__(
        self,
        root: Path | str = ".",
        *,
        policy: SandboxPolicy | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.policy = policy or SandboxPolicy()
        self.nlp = NLPSuite()
        self.tools = ToolLibrary(self.root, nlp=self.nlp)

    def fulfill(
        self,
        purpose: ForgePurpose,
        *,
        forge_if_needed: bool = True,
        persist: bool = True,
        max_repairs: int = 3,
        tool_name: str | None = None,
        chain_steps: Sequence[str] | None = None,
    ) -> FulfillResult:
        grounding = ground_purpose(purpose, nlp=self.nlp)
        evidence = list(grounding.evidence)
        discovered = discover_for_purpose(purpose)

        if grounding.associative_only and not purpose.allow_associative_only:
            return FulfillResult(
                mode="refused",
                ok=False,
                grounding=grounding,
                discover=discovered,
                evidence=evidence,
                reason="associative-only purpose refused by wisdom/lean-back gate",
            )

        lb = lean_back(purpose, self.tools, grounding=grounding)
        if lb.satisfied:
            return FulfillResult(
                mode="chain",
                ok=True,
                grounding=grounding,
                leanback=lb,
                discover=discovered,
                evidence=evidence
                + [{"type": "leanback", "plan": lb.plan.to_dict() if lb.plan else None}],
                reason="lean-back satisfied purpose with existing tools",
            )

        if not forge_if_needed:
            return FulfillResult(
                mode="refused",
                ok=False,
                grounding=grounding,
                leanback=lb,
                discover=discovered,
                evidence=evidence,
                reason=lb.gap_report or "gap remains; forge disabled",
            )

        fr = forge_tool(
            purpose,
            root=self.root,
            tool_name=tool_name or purpose.name,
            max_repairs=max_repairs,
            policy=self.policy,
            persist=persist,
            evidence=evidence,
            chain_steps=chain_steps or purpose.must_compose,
        )
        if fr.persisted:
            self.tools.reload_natives()
        return FulfillResult(
            mode="forge",
            ok=fr.ok,
            grounding=grounding,
            leanback=lb,
            forge=fr,
            discover=discovered,
            evidence=evidence,
            reason=fr.reason,
        )

    def forge(
        self,
        need: str,
        *,
        persist: bool = True,
        name: str | None = None,
        examples: list[IOExample] | None = None,
        invariants: list[str] | None = None,
        allow_associative_only: bool = False,
        force_forge: bool = False,
        require_native: bool = False,
        template: str = "auto",
        must_compose: Sequence[str] | None = None,
    ) -> FulfillResult | ForgeResult:
        """Fulfill a need; set require_native/force_forge to always create a native."""
        ex = list(examples or [])
        inv = list(invariants or [])
        if not ex and "tokenize" in need.lower() and not require_native:
            ex = [IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})]
            if not inv:
                inv = ["output tokens are lowercase"]
        purpose = ForgePurpose(
            need=need,
            examples=ex,
            invariants=inv,
            name=name,
            allow_associative_only=allow_associative_only,
            require_native=require_native,
            template=template,
            must_compose=list(must_compose) if must_compose else None,
        )
        if force_forge or require_native:
            grounding = ground_purpose(purpose, nlp=self.nlp)
            fr = forge_tool(
                purpose,
                root=self.root,
                tool_name=name,
                policy=self.policy,
                persist=persist,
                evidence=grounding.evidence,
                chain_steps=must_compose,
            )
            if fr.persisted:
                self.tools.reload_natives()
            return fr
        return self.fulfill(purpose, persist=persist, tool_name=name, chain_steps=must_compose)

    def create_native_tool(
        self,
        need: str,
        *,
        name: str,
        examples: list[IOExample] | None = None,
        invariants: list[str] | None = None,
        must_compose: Sequence[str] | None = None,
        template: str = "auto",
        persist: bool = True,
        max_repairs: int = 3,
    ) -> ForgeResult:
        """Always forge + testloop + persist a new native novel tool."""
        fr = create_native_tool(
            need,
            root=self.root,
            name=name,
            examples=examples,
            invariants=invariants,
            must_compose=must_compose,
            template=template,
            persist=persist,
            max_repairs=max_repairs,
            policy=self.policy,
        )
        if fr.persisted:
            self.tools.reload_natives()
        return fr

    def wrap_chain(
        self,
        steps: Sequence[str],
        *,
        name: str,
        need: str | None = None,
        persist: bool = True,
    ) -> ForgeResult:
        """Persist a multi-step chain as one reusable native tool."""
        fr = wrap_chain_as_native(
            steps,
            root=self.root,
            name=name,
            need=need,
            persist=persist,
            policy=self.policy,
        )
        if fr.persisted:
            self.tools.reload_natives()
        return fr

    def run_tool(self, name: str, **kwargs: Any) -> Any:
        return self.tools.run(name, **kwargs)

    def discover(self, purpose: str | ForgePurpose) -> list[dict[str, Any]]:
        return discover_for_purpose(purpose)

    def chain(self, steps: list[str], *, text: str) -> dict[str, Any]:
        return run_chain(self.tools, steps, text=text)

    def backends(self) -> dict[str, bool]:
        return self.nlp.backends()
