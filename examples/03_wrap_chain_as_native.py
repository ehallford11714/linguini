"""Wrap a multi-step NLP chain into one reusable native tool, then run it.

Run:
  PYTHONPATH=src python examples/03_wrap_chain_as_native.py
"""

from __future__ import annotations

from _lib import dump, workspace
from linguini import Linguini


def main() -> int:
    ling = Linguini(root=workspace())
    steps = ["nlp.lowercase_tokens", "nlp.claim_hygiene"]

    fr = ling.wrap_chain(
        steps,
        name="tok_then_hygiene",
        need="chain wrap: lowercase tokens then claim hygiene",
    )
    dump("wrap_result", fr.to_dict())
    if not fr.persisted:
        return 1

    out = ling.run_tool("native.tok_then_hygiene", text="Demand looks like growth so buy")
    dump("native.tok_then_hygiene output", out)

    # Same chain without a native (for comparison)
    chained = ling.chain(steps, text="Demand looks like growth so buy")
    dump("ad-hoc chain (not persisted)", {
        "steps": chained["steps"],
        "final": chained["final"],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
