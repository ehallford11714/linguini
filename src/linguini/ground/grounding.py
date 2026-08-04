"""Ground a ForgePurpose with evidence before lean-back / forge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from linguini.forge.purpose import ForgePurpose
from linguini.suite.nlp import NLPSuite


@dataclass
class GroundingReport:
    purpose_hash: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    associative_only: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "purpose_hash": self.purpose_hash,
            "evidence": list(self.evidence),
            "associative_only": self.associative_only,
            "notes": list(self.notes),
        }


def ground_purpose(purpose: ForgePurpose, *, nlp: NLPSuite | None = None) -> GroundingReport:
    nlp = nlp or NLPSuite()
    evidence: list[dict[str, Any]] = []
    notes: list[str] = []
    associative = False

    evidence.append({"type": "need", "text": purpose.need})
    for i, ex in enumerate(purpose.examples):
        evidence.append({"type": "example", "index": i, "input": ex.input, "expected": ex.expected})
        if isinstance(ex.input, str):
            hygiene = nlp.claim_hygiene(ex.input)
            evidence.append({"type": "nlp.claim_hygiene", "index": i, "result": hygiene})
            if hygiene.get("spurious_causation"):
                associative = True
                notes.append(f"example[{i}] looks like similarity⇒causation leap")

    need_l = purpose.need.lower()
    if "similar" in need_l and "cause" in need_l and not purpose.allow_associative_only:
        associative = True
        notes.append("need mentions similarity and cause without allow_associative_only")

    for inv in purpose.invariants:
        evidence.append({"type": "invariant", "text": inv})

    return GroundingReport(
        purpose_hash=purpose.purpose_hash(),
        evidence=evidence,
        associative_only=associative and not purpose.allow_associative_only,
        notes=notes,
    )
