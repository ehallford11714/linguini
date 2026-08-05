"""Invention lifecycle hooks — fail-closed gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from linguini.invent.lint import LintResult, lint_source
from linguini.invent.plan import InventionPlan
from linguini.sandbox.policy import SandboxPolicy


HookFn = Callable[..., Any]


@dataclass
class HookContext:
    plan: InventionPlan
    source: str = ""
    test_source: str = ""
    lint: Optional[LintResult] = None
    tests_ok: bool = False
    persisted: bool = False
    evidence: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "lint": self.lint.to_dict() if self.lint else None,
            "tests_ok": self.tests_ok,
            "persisted": self.persisted,
            "evidence": list(self.evidence),
            "errors": list(self.errors),
        }


@dataclass
class InventionHooks:
    """Ordered gates: pre_invent → post_plan → post_codegen → post_tests → post_persist."""

    pre_invent: list[HookFn] = field(default_factory=list)
    post_plan: list[HookFn] = field(default_factory=list)
    post_codegen: list[HookFn] = field(default_factory=list)
    post_tests: list[HookFn] = field(default_factory=list)
    post_persist: list[HookFn] = field(default_factory=list)

    def run(self, phase: str, ctx: HookContext) -> HookContext:
        for fn in getattr(self, phase):
            fn(ctx)
        return ctx


def default_hooks(policy: SandboxPolicy | None = None) -> InventionHooks:
    policy = policy or SandboxPolicy()
    hooks = InventionHooks()

    def _post_plan(ctx: HookContext) -> None:
        if not ctx.plan.frozen:
            ctx.plan.freeze()
        ctx.evidence.append(
            {"type": "post_plan", "bounds_hash": ctx.plan.bounds_hash, "skill_id": ctx.plan.skill_id}
        )

    def _post_codegen(ctx: HookContext) -> None:
        ctx.plan.assert_frozen()
        ctx.lint = lint_source(ctx.source, ctx.plan, policy=policy)
        ctx.evidence.append({"type": "post_codegen_lint", **ctx.lint.to_dict()})
        if not ctx.lint.ok:
            ctx.errors.extend(ctx.lint.violations)

    def _post_tests(ctx: HookContext) -> None:
        if not ctx.tests_ok:
            ctx.errors.append("pytest gate failed; refuse persist")
        ctx.evidence.append({"type": "post_tests", "ok": ctx.tests_ok})

    def _post_persist(ctx: HookContext) -> None:
        ctx.evidence.append(
            {
                "type": "post_persist",
                "persisted": ctx.persisted,
                "native": f"native.{ctx.plan.name}",
            }
        )

    hooks.post_plan.append(_post_plan)
    hooks.post_codegen.append(_post_codegen)
    hooks.post_tests.append(_post_tests)
    hooks.post_persist.append(_post_persist)
    return hooks
