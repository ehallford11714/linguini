"""Lean-back: satisfy purpose with existing tools before forging."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from linguini.forge.purpose import ForgePurpose
from linguini.ground.grounding import GroundingReport
from linguini.tools.library import ToolLibrary


@dataclass
class ChainPlan:
    steps: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"steps": list(self.steps), "rationale": self.rationale}


@dataclass
class LeanBackResult:
    satisfied: bool
    plan: Optional[ChainPlan] = None
    outputs: list[Any] = field(default_factory=list)
    gap_report: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "satisfied": self.satisfied,
            "plan": self.plan.to_dict() if self.plan else None,
            "outputs": list(self.outputs),
            "gap_report": self.gap_report,
        }


def _need_matches(need: str, *keywords: str) -> bool:
    n = need.lower()
    return all(k in n for k in keywords) or any(k in n for k in keywords)


def lean_back(
    purpose: ForgePurpose,
    library: ToolLibrary,
    *,
    grounding: GroundingReport | None = None,
) -> LeanBackResult:
    """Try to satisfy purpose examples using existing nlp/builtin tools."""
    need = purpose.need.lower()

    # Refuse forge path later if associative-only (handled by fulfill)
    if grounding and grounding.associative_only and not purpose.allow_associative_only:
        return LeanBackResult(
            satisfied=False,
            gap_report="associative-only purpose refused (wisdom gate); set allow_associative_only to override",
        )

    candidates: list[str] = []
    if "lowercase" in need or ("tokenize" in need and "lower" in need):
        candidates = ["nlp.lowercase_tokens"]
    elif "tokenize" in need and "hygiene" in need:
        candidates = ["nlp.compose_tokenize_hygiene"]
    elif "hygiene" in need or "spurious" in need or "wisdom" in need:
        candidates = ["nlp.claim_hygiene"]
    elif "tokenize" in need:
        candidates = ["nlp.tokenize"]
    else:
        # Heuristic: compose tokenize+hygiene if examples look like dicts with tokens
        if purpose.examples and isinstance(purpose.examples[0].expected, dict):
            exp = purpose.examples[0].expected
            if "tokens" in exp and ("hygiene" in exp or "ok" in exp):
                candidates = ["nlp.compose_tokenize_hygiene"]
            elif "tokens" in exp:
                candidates = ["nlp.lowercase_tokens"]
            elif "spurious_causation" in exp or "ok" in exp:
                candidates = ["nlp.claim_hygiene"]

    if not candidates:
        return LeanBackResult(
            satisfied=False,
            gap_report="no existing tool matched purpose; forge may proceed",
        )

    plan = ChainPlan(steps=candidates, rationale=f"matched need keywords → {candidates}")
    outputs: list[Any] = []
    for ex in purpose.examples:
        text = ex.input if isinstance(ex.input, str) else str(ex.input)
        out = library.run(candidates[0], text=text, input=text)
        outputs.append(out)
        if not _example_ok(out, ex.expected):
            return LeanBackResult(
                satisfied=False,
                plan=plan,
                outputs=outputs,
                gap_report=f"existing tool {candidates[0]} failed purpose example verify",
            )

    return LeanBackResult(satisfied=True, plan=plan, outputs=outputs)


def _example_ok(actual: Any, expected: Any) -> bool:
    if expected is None:
        return True
    if isinstance(expected, dict) and isinstance(actual, dict):
        for k, v in expected.items():
            if k not in actual:
                return False
            if actual[k] != v:
                return False
        return True
    return actual == expected
