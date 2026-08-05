"""Invent natives that combine MCP stubs and (optionally) allowlisted libs.

Run:
  PYTHONPATH=src python examples/06_invent_mcp_and_lib.py
"""

from __future__ import annotations

from _lib import dump, workspace
from linguini import Linguini


def main() -> int:
    ling = Linguini(root=workspace())

    mcp = ling.invent(
        "chain mcp fetch and memory with hygiene compose",
        name="ex_mcp_chain",
        prefer_skill="mcp_chain_wrap",
    )
    dump("invent mcp_chain_wrap", {
        "ok": mcp.ok,
        "persisted": mcp.persisted,
        "skill": mcp.plan.skill_id if mcp.plan else None,
        "bounds_hash": mcp.plan.bounds_hash if mcp.plan else None,
        "reason": mcp.reason,
    })
    if not mcp.persisted:
        return 1

    out = ling.run_tool("native.ex_mcp_chain", text="Ground Acme Corp claim")
    dump("use native.ex_mcp_chain", {
        "novel": out.get("novel"),
        "chain": out.get("chain"),
        "hygiene_ok": (out.get("hygiene") or {}).get("ok"),
    })

    dump("skills", ling.skills())
    dump("libs (allowlist sample)", ling.libs()[:4])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
