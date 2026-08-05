"""Create a novel native tool (entity + hygiene composite) and persist it.

Run:
  PYTHONPATH=src python examples/01_create_novel_tool.py
"""

from __future__ import annotations

from _lib import dump, workspace
from linguini import IOExample, Linguini


def main() -> int:
    root = workspace()
    ling = Linguini(root=root)

    fr = ling.invent(
        "novel claim analyzer: extract entities, lemmas, and causation hygiene",
        name="claim_analyzer",
        prefer_skill="entity_hygiene",
        examples=[
            IOExample(
                input="Acme Corp grew 12%. Demand looks fine.",
                expected={"novel": True},
            )
        ],
    )
    dump("forge_result", fr.to_dict())
    if not fr.persisted:
        print("FAILED: tool was not persisted")
        return 1

    print(f"\nPersisted as {fr.native_name}")
    print(f"Registry: {root / '.linguini' / 'native_tools' / 'registry.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
