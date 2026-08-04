"""Soft NLP suite adapters — heuristic always; soft heavy backends when installed."""

from __future__ import annotations

import hashlib
import importlib.util
import re
from typing import Any

from linguini.ir.batch import LinguaBatch

_WORD = re.compile(r"[A-Za-z0-9']+")
_SENT = re.compile(r"[^.!?]+[.!?]?")
_ENTITY = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+|\d+(?:\.\d+)?%?|\$\d+(?:,\d{3})*(?:\.\d+)?)\b"
)


def detect_backends() -> dict[str, bool]:
    names = ("spacy", "transformers", "gensim", "nltk", "stanza", "flair", "fasttext")
    return {n: importlib.util.find_spec(n) is not None for n in names}


class NLPSuite:
    """Composable NLP ops used as forge material and lean-back targets."""

    def backends(self) -> dict[str, bool]:
        return detect_backends()

    def tokenize(self, text: str) -> list[str]:
        return _WORD.findall(text)

    def lowercase_tokens(self, text: str) -> list[str]:
        return [t.lower() for t in self.tokenize(text)]

    def sentences(self, text: str) -> list[str]:
        parts = [s.strip() for s in _SENT.findall(text) if s.strip()]
        return parts or ([text.strip()] if text.strip() else [])

    def entities(self, text: str) -> list[dict[str, str]]:
        found = []
        for m in _ENTITY.finditer(text):
            val = m.group(1)
            kind = "MONEY" if val.startswith("$") else "PERCENT" if val.endswith("%") else "ENTITY"
            found.append({"text": val, "label": kind})
        return found

    def lemmas(self, text: str) -> list[str]:
        # Heuristic lemma: lowercase + light plural strip
        out = []
        for t in self.lowercase_tokens(text):
            if len(t) > 3 and t.endswith("ies"):
                out.append(t[:-3] + "y")
            elif len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
                out.append(t[:-1])
            else:
                out.append(t)
        return out

    def topic_hash(self, text: str, *, dim: int = 16) -> list[float]:
        vec = [0.0] * dim
        for t in self.lowercase_tokens(text):
            h = hashlib.sha256(t.encode("utf-8")).hexdigest()
            idx = int(h[:8], 16) % dim
            sign = 1.0 if int(h[8:10], 16) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def batch_tokenize(self, batch: LinguaBatch) -> LinguaBatch:
        batch.tokens = [self.tokenize(t) for t in batch.texts]
        batch.lemmas = [self.lemmas(t) for t in batch.texts]
        return batch

    def claim_hygiene(self, text: str) -> dict[str, Any]:
        """Flag similarity→causation leaps (heuristic)."""
        lower = text.lower()
        spur = bool(
            re.search(r"\b(looks? like|similar to|same as)\b", lower)
            and re.search(r"\b(so|therefore|thus|cause|causes|will)\b", lower)
        )
        return {
            "text": text,
            "spurious_causation": spur,
            "ok": not spur,
            "band": "associative" if spur else "neutral",
        }

    def compose_tokenize_hygiene(self, text: str) -> dict[str, Any]:
        tokens = self.lowercase_tokens(text)
        hygiene = self.claim_hygiene(text)
        return {"tokens": tokens, "hygiene": hygiene, "ok": hygiene["ok"]}

    def compose_entity_hygiene(self, text: str) -> dict[str, Any]:
        """Novel-style composite: entities + hygiene + lemmas."""
        return {
            "tokens": self.lowercase_tokens(text),
            "lemmas": self.lemmas(text),
            "entities": self.entities(text),
            "hygiene": self.claim_hygiene(text),
            "topics": self.topic_hash(text),
            "sentences": self.sentences(text),
            "ok": self.claim_hygiene(text)["ok"],
            "novel": True,
        }

    def analyze(self, text: str) -> dict[str, Any]:
        return self.compose_entity_hygiene(text)

    def op_names(self) -> list[str]:
        return [
            "nlp.tokenize",
            "nlp.lowercase_tokens",
            "nlp.sentences",
            "nlp.entities",
            "nlp.lemmas",
            "nlp.topic_hash",
            "nlp.batch_tokenize",
            "nlp.claim_hygiene",
            "nlp.compose_tokenize_hygiene",
            "nlp.compose_entity_hygiene",
            "nlp.analyze",
        ]

    def run(self, op: str, **kwargs: Any) -> Any:
        key = op.removeprefix("nlp.")
        text = str(kwargs.get("text") or kwargs.get("input") or "")
        dispatch = {
            "tokenize": lambda: self.tokenize(text),
            "lowercase_tokens": lambda: self.lowercase_tokens(text),
            "sentences": lambda: self.sentences(text),
            "entities": lambda: self.entities(text),
            "lemmas": lambda: self.lemmas(text),
            "topic_hash": lambda: self.topic_hash(text),
            "claim_hygiene": lambda: self.claim_hygiene(text),
            "compose_tokenize_hygiene": lambda: self.compose_tokenize_hygiene(text),
            "compose_entity_hygiene": lambda: self.compose_entity_hygiene(text),
            "analyze": lambda: self.analyze(text),
        }
        if key == "batch_tokenize":
            batch = kwargs.get("batch")
            if isinstance(batch, LinguaBatch):
                return self.batch_tokenize(batch)
            return self.batch_tokenize(LinguaBatch.from_text(text))
        if key not in dispatch:
            raise KeyError(f"Unknown NLP op: {op}")
        return dispatch[key]()
