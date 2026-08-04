"""Columnar LinguaBatch IR — bridge across NLP backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LinguaBatch:
    texts: list[str]
    doc_ids: list[str] = field(default_factory=list)
    tokens: list[list[str]] = field(default_factory=list)
    lemmas: list[list[str]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.doc_ids:
            self.doc_ids = [f"d{i}" for i in range(len(self.texts))]

    @classmethod
    def from_text(cls, text: str, *, doc_id: str = "d0") -> "LinguaBatch":
        return cls(texts=[text], doc_ids=[doc_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_ids": list(self.doc_ids),
            "texts": list(self.texts),
            "tokens": [list(t) for t in self.tokens],
            "lemmas": [list(t) for t in self.lemmas],
            "meta": dict(self.meta),
        }
