"""Linguini CLI — invent, forge, chain, discover."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from linguini import __version__
from linguini.api import Linguini


def _print(obj: object) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="linguini",
        description="Invent native tools from MCP + libs + skills (lean-back first, verify always)",
    )
    p.add_argument("--version", action="version", version=f"linguini {__version__}")
    p.add_argument("--root", default=".", help="Project root (native tools under .linguini/)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("backends", help="Show detected NLP backends")

    tl = sub.add_parser("tools", help="List or run tools")
    tl_sub = tl.add_subparsers(dest="tools_cmd", required=True)
    tlist = tl_sub.add_parser("list")
    tlist.add_argument("--layer", default=None)
    trun = tl_sub.add_parser("run")
    trun.add_argument("name")
    trun.add_argument("--text", required=True)

    disc = sub.add_parser("discover", help="Discover purpose-aligned MCP servers")
    disc.add_argument("--purpose", required=True)

    sk = sub.add_parser("skills", help="List invention skills (recipes)")
    sk_sub = sk.add_subparsers(dest="skills_cmd", required=True)
    sk_sub.add_parser("list")

    lb = sub.add_parser("libs", help="List allowlisted pip packages")
    lb_sub = lb.add_subparsers(dest="libs_cmd", required=True)
    lb_sub.add_parser("list")

    ch = sub.add_parser("chain", help="Run a local tool chain")
    ch.add_argument("--steps", required=True, help="Comma-separated tool names")
    ch.add_argument("--text", required=True)

    inv = sub.add_parser("invent", help="Invent a novel tool (compose → lint → pytest → persist)")
    inv.add_argument("--need", required=True)
    inv.add_argument("--name", required=True)
    inv.add_argument("--skill", default=None, help="Prefer skill id")
    inv.add_argument("--llm", action="store_true", help="Allow bounded LLM fill (needs API key)")
    inv.add_argument("--no-persist", action="store_true")

    fg = sub.add_parser("forge", help="Fulfill purpose: lean-back or invent/forge+persist")
    fg.add_argument("--need", required=True)
    fg.add_argument("--name", default=None)
    fg.add_argument("--force", action="store_true", help="Skip lean-back; always invent")
    fg.add_argument("--native", action="store_true", help="Require a new native tool")
    fg.add_argument("--template", default="auto")
    fg.add_argument("--steps", default=None)
    fg.add_argument("--no-persist", action="store_true")

    cr = sub.add_parser("create", help="Create native via inventor (alias of invent)")
    cr.add_argument("--need", required=True)
    cr.add_argument("--name", required=True)
    cr.add_argument("--template", default="auto")
    cr.add_argument("--steps", default=None)
    cr.add_argument("--llm", action="store_true")
    cr.add_argument("--no-persist", action="store_true")

    wc = sub.add_parser("wrap-chain", help="Persist a tool chain as one native")
    wc.add_argument("--steps", required=True)
    wc.add_argument("--name", required=True)
    wc.add_argument("--need", default=None)
    wc.add_argument("--no-persist", action="store_true")

    hy = sub.add_parser("hygiene", help="Secondary CARAG / Netrin helpers")
    hy.add_argument("kind", choices=["carag", "netrin"])
    hy.add_argument("--text", required=True)

    sub.add_parser("mcp", help="Run Linguini MCP stdio server")

    args = p.parse_args(argv)
    root = Path(args.root)
    ling = Linguini(root=root)

    if args.cmd == "backends":
        _print(ling.backends())
        return 0
    if args.cmd == "tools":
        if args.tools_cmd == "list":
            _print(ling.tools.list(layer=args.layer))
            return 0
        _print(ling.run_tool(args.name, text=args.text))
        return 0
    if args.cmd == "discover":
        _print(ling.discover(args.purpose))
        return 0
    if args.cmd == "skills":
        _print(ling.skills())
        return 0
    if args.cmd == "libs":
        _print(ling.libs())
        return 0
    if args.cmd == "chain":
        steps = [s.strip() for s in args.steps.split(",") if s.strip()]
        _print(ling.chain(steps, text=args.text))
        return 0
    if args.cmd == "invent":
        fr = ling.invent(
            args.need,
            name=args.name,
            use_llm=bool(args.llm),
            prefer_skill=args.skill,
            persist=not args.no_persist,
        )
        _print(fr.to_dict())
        return 0 if fr.ok else 1
    if args.cmd == "forge":
        steps = (
            [s.strip() for s in args.steps.split(",") if s.strip()] if args.steps else None
        )
        result = ling.forge(
            args.need,
            name=args.name,
            persist=not args.no_persist,
            force_forge=bool(args.force),
            require_native=bool(args.native),
            template=args.template,
            must_compose=steps,
        )
        _print(result.to_dict() if hasattr(result, "to_dict") else result)
        return 0 if getattr(result, "ok", False) else 1
    if args.cmd == "create":
        fr = ling.create_native_tool(
            args.need,
            name=args.name,
            template=args.template,
            persist=not args.no_persist,
            use_llm=bool(args.llm),
        )
        _print(fr.to_dict())
        return 0 if fr.ok else 1
    if args.cmd == "wrap-chain":
        steps = [s.strip() for s in args.steps.split(",") if s.strip()]
        fr = ling.wrap_chain(
            steps,
            name=args.name,
            need=args.need,
            persist=not args.no_persist,
        )
        _print(fr.to_dict())
        return 0 if fr.ok else 1
    if args.cmd == "hygiene":
        if args.kind == "carag":
            from linguini.hygiene.carag import build_carag

            _print(build_carag(args.text, nlp=ling.nlp).to_dict())
            return 0
        from linguini.hygiene.netrin import netrin_route

        _print(netrin_route(args.text, nlp=ling.nlp).to_dict())
        return 0
    if args.cmd == "mcp":
        from linguini.mcp.server import main as mcp_main

        return mcp_main(["--root", str(root.resolve())])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
