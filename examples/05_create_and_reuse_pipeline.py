"""End-to-end pipeline: create several natives, list them, run, and chain.

Run:
  PYTHONPATH=src python examples/05_create_and_reuse_pipeline.py
"""

from __future__ import annotations

from _lib import dump, workspace
from linguini import Linguini


def main() -> int:
    ling = Linguini(root=workspace())

    created = []
    for need, name, template in [
        ("novel entity hygiene analyzer", "pipeline_entity", "entity_hygiene"),
        ("novel tokenize hygiene composite", "pipeline_tok_hygiene", "tokenize_hygiene"),
    ]:
        fr = ling.create_native_tool(need, name=name, template=template)
        created.append(fr.to_dict())
        if not fr.persisted:
            dump("failed", fr.to_dict())
            return 1

    dump("created", [{"name": c["native_name"], "ok": c["ok"]} for c in created])
    dump("all native tools", ling.tools.list(layer="native"))

    text = "Acme Corp grew 12%. Demand looks like last year so expand."
    for name in ("native.pipeline_entity", "native.pipeline_tok_hygiene"):
        out = ling.run_tool(name, text=text)
        dump(f"use {name}", {
            "novel": out.get("novel"),
            "tokens": out.get("tokens"),
            "entities": out.get("entities"),
            "hygiene_ok": (out.get("hygiene") or {}).get("ok", out.get("ok")),
        })

    # Chain a library op into a native
    chained = ling.chain(
        ["nlp.sentences", "native.pipeline_entity"],
        text=text,
    )
    dump("chain nlp.sentences -> native.pipeline_entity", {
        "steps": chained["steps"],
        "final_keys": list(chained["final"].keys()) if isinstance(chained["final"], dict) else type(chained["final"]).__name__,
    })

    # Discover MCP servers aligned to the purpose (offline fixture)
    dump("discover", ling.discover("grounding docs fetch entities hygiene"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
