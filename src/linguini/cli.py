"""Linguini CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from linguini import __version__
from linguini.api import Linguini
from linguini.forge.purpose import ForgePurpose, IOExample


def _print(obj: object) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="linguini", description="Forge native NLP tools with lean-back + verify")
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

    disc = sub.add_parser("discover", help="Discover purpose-aligned MCP servers (fixture catalog)")
    disc.add_argument("--purpose", required=True)

    ch = sub.add_parser("chain", help="Run a local tool chain")
    ch.add_argument("--steps", required=True, help="Comma-separated tool names")
    ch.add_argument("--text", required=True)

    fg = sub.add_parser("forge", help="Fulfill purpose: lean-back or forge+testloop+persist")
    fg.add_argument("--need", required=True)
    fg.add_argument("--name", default=None)
    fg.add_argument("--force", action="store_true", help="Skip lean-back; always forge")
    fg.add_argument("--no-persist", action="store_true")

    args = p.parse_args(argv)
    ling = Linguini(root=Path(args.root))

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
    if args.cmd == "chain":
        steps = [s.strip() for s in args.steps.split(",") if s.strip()]
        _print(ling.chain(steps, text=args.text))
        return 0
    if args.cmd == "forge":
        result = ling.forge(
            args.need,
            name=args.name,
            persist=not args.no_persist,
            force_forge=bool(args.force),
        )
        _print(result.to_dict() if hasattr(result, "to_dict") else result)
        return 0 if (getattr(result, "ok", False)) else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
