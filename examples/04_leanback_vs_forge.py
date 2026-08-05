"""Show lean-back (reuse library) vs require_native (forge a new tool).

Run:
  PYTHONPATH=src python examples/04_leanback_vs_forge.py
"""

from __future__ import annotations

from _lib import dump, workspace
from linguini import ForgePurpose, IOExample, Linguini


def main() -> int:
    ling = Linguini(root=workspace())

    # 1) Existing NLP op already satisfies purpose → mode=chain, no new native
    lean = ling.fulfill(
        ForgePurpose(
            need="tokenize and lowercase text",
            examples=[
                IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})
            ],
            invariants=["output tokens are lowercase"],
        )
    )
    dump("lean-back fulfill", {
        "mode": lean.mode,
        "ok": lean.ok,
        "reason": lean.reason,
        "plan": lean.leanback.plan.to_dict() if lean.leanback and lean.leanback.plan else None,
    })

    # 2) Same need but invent → always compose skill + persist a novel op
    fr = ling.invent(
        "tokenize and lowercase text as a novel native",
        name="forced_lower_tokens",
        prefer_skill="lowercase_tokens",
        examples=[
            IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})
        ],
    )
    dump("invent (force novel native)", {
        "ok": fr.ok,
        "persisted": fr.persisted,
        "native_name": fr.native_name,
        "reason": fr.reason,
    })

    if fr.persisted:
        out = ling.run_tool("native.forced_lower_tokens", text="Hello World")
        dump("use forged native", out)

    return 0 if lean.ok and fr.ok and lean.mode == "chain" and fr.persisted else 1


if __name__ == "__main__":
    raise SystemExit(main())
