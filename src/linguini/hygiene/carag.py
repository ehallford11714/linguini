"""Minimal CARAG dual-band pack — secondary hygiene helper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from linguini.suite.nlp import NLPSuite


@dataclass
class CARAGPack:
    query: str
    semantic_neighbors: list[str] = field(default_factory=list)
    associative_paths: list[str] = field(default_factory=list)
    causal_skeleton: list[dict[str, Any]] = field(default_factory=list)
    wisdom_guardrails: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "semantic_neighbors": list(self.semantic_neighbors),
            "associative_paths": list(self.associative_paths),
            "causal_skeleton": list(self.causal_skeleton),
            "wisdom_guardrails": list(self.wisdom_guardrails),
        }


def build_carag(query: str, *, nlp: NLPSuite | None = None) -> CARAGPack:
    nlp = nlp or NLPSuite()
    tokens = nlp.lowercase_tokens(query)
    hygiene = nlp.claim_hygiene(query)
    neighbors = tokens[:8]
    assoc = [" ~ ".join(tokens[i : i + 2]) for i in range(max(0, len(tokens) - 1))][:5]
    causal: list[dict[str, Any]] = []
    guards = ["association is not causation"]
    if hygiene["spurious_causation"]:
        guards.append("reject similarity⇒cause justification")
    else:
        # Weak heuristic causal cue: explicit effect language without similarity
        if any(w in query.lower() for w in ("effect of", "if we", "intervention", "causes")):
            causal.append({"edge": "intervention→outcome", "confidence": 0.4, "status": "candidate"})
    return CARAGPack(
        query=query,
        semantic_neighbors=neighbors,
        associative_paths=assoc,
        causal_skeleton=causal,
        wisdom_guardrails=guards,
    )
