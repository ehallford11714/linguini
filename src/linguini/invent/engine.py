"""Tool inventor engine — compose → (LLM fill) → lint → pytest → persist."""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from linguini.forge.persist import persist_native
from linguini.forge.purpose import ForgePurpose, IOExample
from linguini.ground.grounding import ground_purpose
from linguini.invent.catalogs import skill_by_id
from linguini.invent.codegen import purpose_from_plan_examples
from linguini.invent.composer import compose_plan
from linguini.invent.deps import ensure_plan_deps, resolve_pytest_python
from linguini.invent.hooks import HookContext, InventionHooks, default_hooks
from linguini.invent.llm_fill import FillResult, bounded_fill
from linguini.invent.plan import InventionBrief, InventionPlan
from linguini.leanback.planner import lean_back
from linguini.sandbox.policy import SandboxPolicy
from linguini.suite.nlp import NLPSuite
from linguini.tools.library import ToolLibrary


@dataclass
class InventResult:
    ok: bool
    persisted: bool
    mode: str  # chain | invent | refused
    tool_name: str = ""
    native_name: str = ""
    plan: Optional[InventionPlan] = None
    fill: Optional[FillResult] = None
    lint_ok: bool = False
    tests_ok: bool = False
    deps: Optional[dict[str, Any]] = None
    entry: Optional[dict[str, Any]] = None
    reason: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "persisted": self.persisted,
            "mode": self.mode,
            "tool_name": self.tool_name,
            "native_name": self.native_name,
            "plan": self.plan.to_dict() if self.plan else None,
            "fill": self.fill.to_dict() if self.fill else None,
            "lint_ok": self.lint_ok,
            "tests_ok": self.tests_ok,
            "deps": self.deps,
            "entry": self.entry,
            "reason": self.reason,
            "evidence": list(self.evidence),
            "stdout": self.stdout[-4000:],
            "stderr": self.stderr[-4000:],
        }


def _ensure_examples(purpose: ForgePurpose, plan: InventionPlan) -> ForgePurpose:
    if purpose.examples:
        return purpose
    skill = skill_by_id(plan.skill_id)
    purpose.examples = purpose_from_plan_examples(plan, skill)
    if not purpose.invariants and plan.template in {"lowercase_tokens", "tokenize_hygiene", "entity_hygiene"}:
        purpose.invariants = ["output tokens are lowercase"]
    return purpose


def _run_pytest(work: Path, python: str, timeout: float) -> tuple[int, str, str]:
    env_pythonpath = str(Path(__file__).resolve().parents[1])  # src/linguini -> need src
    src = str(Path(__file__).resolve().parents[2])  # src
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [python, "-m", "pytest", "-q", str(work / "test_native.py")],
        cwd=str(work),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def invent_tool(
    purpose: ForgePurpose,
    *,
    root: Path | str,
    name: str,
    brief: InventionBrief | None = None,
    persist: bool = True,
    policy: SandboxPolicy | None = None,
    library: ToolLibrary | None = None,
    nlp: NLPSuite | None = None,
    hooks: InventionHooks | None = None,
    skip_leanback: bool = False,
    allow_pip_install: bool = True,
) -> InventResult:
    """
    Main inventor entry: lean-back → compose plan → fill → lint → deps → pytest → persist.
    """
    root = Path(root)
    policy = policy or SandboxPolicy()
    brief = brief or InventionBrief()
    nlp = nlp or NLPSuite()
    library = library or ToolLibrary(root, nlp=nlp)
    hooks = hooks or default_hooks(policy)

    grounding = ground_purpose(purpose, nlp=nlp)
    evidence = list(grounding.evidence)

    if grounding.associative_only and not purpose.allow_associative_only:
        return InventResult(
            ok=False,
            persisted=False,
            mode="refused",
            reason="associative-only purpose refused",
            evidence=evidence,
        )

    if not skip_leanback and not purpose.require_native and not brief.use_llm:
        # Still lean-back for simple needs unless invent is forced via require_native / prefer_skill
        if not brief.prefer_skill:
            lb = lean_back(purpose, library, grounding=grounding)
            if lb.satisfied:
                return InventResult(
                    ok=True,
                    persisted=False,
                    mode="chain",
                    reason="lean-back satisfied; no invent",
                    evidence=evidence
                    + [{"type": "leanback", "plan": lb.plan.to_dict() if lb.plan else None}],
                )

    plan = compose_plan(purpose, name=name, brief=brief)
    purpose = _ensure_examples(purpose, plan)
    ctx = HookContext(plan=plan, evidence=list(evidence))
    hooks.run("pre_invent", ctx)
    hooks.run("post_plan", ctx)

    fill = bounded_fill(plan, purpose, use_llm=brief.use_llm, policy=policy, max_repairs=1)
    ctx.source = fill.source
    ctx.test_source = fill.test_source
    hooks.run("post_codegen", ctx)

    if fill.refused or (ctx.lint and not ctx.lint.ok):
        return InventResult(
            ok=False,
            persisted=False,
            mode="refused",
            tool_name=name,
            native_name=f"native.{name}",
            plan=plan,
            fill=fill,
            lint_ok=False,
            reason=fill.reason or "; ".join(ctx.errors),
            evidence=ctx.evidence,
        )

    open_pip = bool(brief.open_pip or getattr(policy, "allow_open_pip", False))
    open_npm = bool(brief.open_npm or getattr(policy, "allow_open_npm", False))
    # Open installs need network to hit registries
    allow_network = bool(policy.allow_network or open_pip or open_npm)

    deps_result = ensure_plan_deps(
        root,
        pip_deps=plan.pip_deps,
        npm_deps=plan.npm_deps,
        allow_pip_install=allow_pip_install and getattr(policy, "allow_pip_install", True),
        allow_npm_install=getattr(policy, "allow_npm_install", True),
        allow_open_pip=open_pip,
        allow_open_npm=open_npm,
        allow_network=allow_network,
    )
    if (plan.pip_deps or plan.npm_deps) and not deps_result.ok:
        return InventResult(
            ok=False,
            persisted=False,
            mode="refused",
            tool_name=name,
            native_name=f"native.{name}",
            plan=plan,
            fill=fill,
            lint_ok=True,
            deps=deps_result.to_dict(),
            reason="pip/npm install failed: " + "; ".join(deps_result.errors),
            evidence=ctx.evidence,
        )

    python = resolve_pytest_python(root, prefer_forge=bool(plan.pip_deps))
    # If no forge pip deps, use current interpreter (faster for pure nlp / npm-only)
    if not plan.pip_deps:
        import sys

        python = sys.executable

    # Expose root for node_proxy forge_node resolution during pytest
    import os

    os.environ["LINGUINI_ROOT"] = str(root)

    tests_ok = False
    stdout = stderr = ""
    with tempfile.TemporaryDirectory(prefix="linguini_invent_") as tmp:
        work = Path(tmp)
        (work / "TOOL_MODULE.py").write_text(fill.source, encoding="utf-8")
        (work / "test_native.py").write_text(fill.test_source, encoding="utf-8")
        code, stdout, stderr = _run_pytest(work, python, policy.pytest_timeout_s)
        tests_ok = code == 0

    ctx.tests_ok = tests_ok
    hooks.run("post_tests", ctx)

    if not tests_ok:
        return InventResult(
            ok=False,
            persisted=False,
            mode="invent",
            tool_name=name,
            native_name=f"native.{name}",
            plan=plan,
            fill=fill,
            lint_ok=True,
            tests_ok=False,
            deps=deps_result.to_dict(),
            reason="unit-test loop failed; nothing persisted",
            evidence=ctx.evidence,
            stdout=stdout,
            stderr=stderr,
        )

    entry = None
    persisted = False
    if persist:
        entry = persist_native(
            root,
            tool_name=name,
            source=fill.source,
            test_source=fill.test_source,
            purpose=purpose,
            description=purpose.need,
        )
        persisted = True
        library.reload_natives()

    ctx.persisted = persisted
    hooks.run("post_persist", ctx)

    return InventResult(
        ok=True,
        persisted=persisted,
        mode="invent",
        tool_name=name,
        native_name=f"native.{name}",
        plan=plan,
        fill=fill,
        lint_ok=True,
        tests_ok=True,
        deps=deps_result.to_dict(),
        entry=entry,
        reason="invented and persisted after lint+pytest" if persisted else "tests passed; persist=False",
        evidence=ctx.evidence,
        stdout=stdout,
        stderr=stderr,
    )


def invent(
    need: str,
    *,
    root: Path | str,
    name: str,
    use_llm: bool = False,
    prefer_skill: str | None = None,
    examples: list[IOExample] | None = None,
    persist: bool = True,
    policy: SandboxPolicy | None = None,
    require_native: bool = True,
    open_pip: bool = False,
    open_npm: bool = False,
) -> InventResult:
    purpose = ForgePurpose(
        need=need,
        name=name,
        examples=list(examples or []),
        require_native=require_native,
    )
    brief = InventionBrief(
        use_llm=use_llm,
        prefer_skill=prefer_skill,
        open_pip=open_pip,
        open_npm=open_npm,
    )
    if open_pip or open_npm:
        policy = policy or SandboxPolicy()
        policy.allow_open_pip = policy.allow_open_pip or open_pip
        policy.allow_open_npm = policy.allow_open_npm or open_npm
        policy.allow_network = True
    return invent_tool(purpose, root=root, name=name, brief=brief, persist=persist, policy=policy, skip_leanback=True)
