"""Use a previously forged native tool (creates it first if missing).

Run:
  PYTHONPATH=src python examples/02_use_novel_tool.py
"""

from __future__ import annotations

from _lib import dump, workspace
from linguini import Linguini


TOOL = "native.claim_analyzer"
SAMPLES = [
    "Acme Corp grew 12%. Hello World",
    "Demand looks like last quarter so raise price",
    "If we cut price, units sold should rise.",
]


def ensure_tool(ling: Linguini) -> None:
    names = {t["name"] for t in ling.tools.list(layer="native")}
    if TOOL in names:
        return
    fr = ling.create_native_tool(
        "novel claim analyzer: extract entities, lemmas, and causation hygiene",
        name="claim_analyzer",
        template="entity_hygiene",
    )
    if not fr.persisted:
        raise SystemExit(f"could not create {TOOL}: {fr.reason}")


def main() -> int:
    ling = Linguini(root=workspace())
    ensure_tool(ling)

    dump("native_tools", ling.tools.list(layer="native"))
    for text in SAMPLES:
        out = ling.run_tool(TOOL, text=text)
        dump(f"run({text!r})", {
            "novel": out.get("novel"),
            "tokens": out.get("tokens"),
            "entities": out.get("entities"),
            "hygiene": out.get("hygiene"),
            "ok": out.get("ok"),
        })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
