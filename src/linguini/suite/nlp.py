"""Soft NLP suite adapters — heuristic always available."""

from __future__ import annotations

import importlib.util
import re
from typing import Any

from linguini.ir.batch import LinguaBatch

_WORD = re.compile(r"[A-Za-z0-9']+")


def detect_backends() -> dict[str, bool]:
    names = ("spacy", "transformers", "gensim", "nltk", "stanza", "flair")
    return {n: importlib.util.find_spec(n) is not None for n in names}


class NLPSuite:
    """Composable NLP ops used as forge material and lean-back targets."""

    def backends(self) -> dict[str, bool]:
        return detect_backends()

    def tokenize(self, text: str) -> list[str]:
        return _WORD.findall(text)

    def lowercase_tokens(self, text: str) -> list[str]:
        return [t.lower() for t in self.tokenize(text)]

    def batch_tokenize(self, batch: LinguaBatch) -> LinguaBatch:
        batch.tokens = [self.tokenize(t) for t in batch.texts]
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

    def op_names(self) -> list[str]:
        return [
            "nlp.tokenize",
            "nlp.lowercase_tokens",
            "nlp.batch_tokenize",
            "nlp.claim_hygiene",
            "nlp.compose_tokenize_hygiene",
        ]

    def run(self, op: str, **kwargs: Any) -> Any:
        key = op.removeprefix("nlp.")
        text = str(kwargs.get("text") or kwargs.get("input") or "")
        if key == "tokenize":
            return self.tokenize(text)
        if key == "lowercase_tokens":
            return self.lowercase_tokens(text)
        if key == "claim_hygiene":
            return self.claim_hygiene(text)
        if key == "compose_tokenize_hygiene":
            return self.compose_tokenize_hygiene(text)
        raise KeyError(f"Unknown NLP op: {op}")
