"""Purpose contract that drives forge + lean-back verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class IOExample:
    input: Any
    expected: Any
    note: str = ""


@dataclass
class ForgePurpose:
    need: str
    examples: list[IOExample] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    allowed_imports: list[str] = field(default_factory=list)
    must_compose: Optional[list[str]] = None
    allow_associative_only: bool = False
    name: Optional[str] = None

    def purpose_hash(self) -> str:
        payload = {
            "need": self.need,
            "examples": [asdict(e) for e in self.examples],
            "invariants": list(self.invariants),
        }
        blob = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "need": self.need,
            "examples": [asdict(e) for e in self.examples],
            "invariants": list(self.invariants),
            "allowed_imports": list(self.allowed_imports),
            "must_compose": list(self.must_compose or []),
            "allow_associative_only": self.allow_associative_only,
            "name": self.name,
            "purpose_hash": self.purpose_hash(),
        }
