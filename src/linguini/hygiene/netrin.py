"""Minimal Netrin-style routing packet — secondary hygiene helper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from linguini.hygiene.carag import CARAGPack, build_carag
from linguini.suite.nlp import NLPSuite

Verdict = Literal["CONVERGENT", "DIVERGENT", "EXPLORATORY"]


@dataclass
class NetrinPacket:
    morphemes: list[dict[str, str]] = field(default_factory=list)
    verdict: Verdict = "EXPLORATORY"
    confidence: float = 0.5
    temperature: float = 0.8
    posture: str = "explore"

    def to_dict(self) -> dict[str, Any]:
        return {
            "morphemes": list(self.morphemes),
            "verdict": self.verdict,
            "confidence": self.confidence,
            "temperature": self.temperature,
            "posture": self.posture,
        }


def netrin_route(query: str, *, pack: CARAGPack | None = None, nlp: NLPSuite | None = None) -> NetrinPacket:
    nlp = nlp or NLPSuite()
    pack = pack or build_carag(query, nlp=nlp)
    morphs: list[dict[str, str]] = []
    for t in pack.semantic_neighbors[:6]:
        morphs.append({"token": t, "role": "drift"})
    for edge in pack.causal_skeleton:
        morphs.append({"token": str(edge.get("edge")), "role": "attract"})
    if any("reject" in g for g in pack.wisdom_guardrails):
        morphs.append({"token": "spurious_cause", "role": "repel"})
        verdict: Verdict = "DIVERGENT"
        conf = 0.7
    elif pack.causal_skeleton:
        verdict = "CONVERGENT"
        conf = 0.65
    else:
        verdict = "EXPLORATORY"
        conf = 0.45
    # Confidence-gated temperature (Netrin-style)
    temp = max(0.2, min(1.25, 1.25 - conf * 0.75))
    posture = {"CONVERGENT": "lean_in", "DIVERGENT": "push_back", "EXPLORATORY": "hedge"}[verdict]
    return NetrinPacket(
        morphemes=morphs,
        verdict=verdict,
        confidence=conf,
        temperature=temp,
        posture=posture,
    )
