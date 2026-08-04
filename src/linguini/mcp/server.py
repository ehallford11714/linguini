"""Linguini MCP stdio server — exposes forge / create_native / tools / chain / discover."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from linguini.api import Linguini

SERVER_NAME = "linguini"
SERVER_VERSION = "0.1.2"

TOOLS: list[dict[str, Any]] = [
    {
        "name": "linguini_backends",
        "description": "List detected NLP backends",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "linguini_tools_list",
        "description": "List tools in the library (nlp/builtin/native)",
        "inputSchema": {
            "type": "object",
            "properties": {"layer": {"type": "string"}},
        },
    },
    {
        "name": "linguini_tools_run",
        "description": "Run a named tool",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["name", "text"],
        },
    },
    {
        "name": "linguini_discover",
        "description": "Discover purpose-aligned MCP servers from catalog",
        "inputSchema": {
            "type": "object",
            "properties": {"purpose": {"type": "string"}},
            "required": ["purpose"],
        },
    },
    {
        "name": "linguini_chain",
        "description": "Run a local tool chain",
        "inputSchema": {
            "type": "object",
            "properties": {
                "steps": {"type": "array", "items": {"type": "string"}},
                "text": {"type": "string"},
            },
            "required": ["steps", "text"],
        },
    },
    {
        "name": "linguini_forge",
        "description": "Fulfill a purpose (lean-back or forge). Set require_native to create a native.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "need": {"type": "string"},
                "name": {"type": "string"},
                "require_native": {"type": "boolean"},
                "force": {"type": "boolean"},
                "persist": {"type": "boolean"},
                "template": {"type": "string"},
            },
            "required": ["need"],
        },
    },
    {
        "name": "linguini_create_native",
        "description": "Always create a new native novel tool (testloop + persist on green)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "need": {"type": "string"},
                "name": {"type": "string"},
                "template": {"type": "string"},
                "steps": {"type": "array", "items": {"type": "string"}},
                "persist": {"type": "boolean"},
            },
            "required": ["need", "name"],
        },
    },
    {
        "name": "linguini_wrap_chain",
        "description": "Persist a multi-step chain as one native tool",
        "inputSchema": {
            "type": "object",
            "properties": {
                "steps": {"type": "array", "items": {"type": "string"}},
                "name": {"type": "string"},
                "need": {"type": "string"},
                "persist": {"type": "boolean"},
            },
            "required": ["steps", "name"],
        },
    },
]


def _ok_text(payload: Any) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2, default=str)}],
        "isError": False,
    }


def _err_text(msg: str) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": msg}],
        "isError": True,
    }


def handle_tool(ling: "Linguini", name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    args = arguments or {}
    try:
        if name == "linguini_backends":
            return _ok_text(ling.backends())
        if name == "linguini_tools_list":
            return _ok_text(ling.tools.list(layer=args.get("layer")))
        if name == "linguini_tools_run":
            return _ok_text(ling.run_tool(str(args["name"]), text=str(args.get("text", ""))))
        if name == "linguini_discover":
            return _ok_text(ling.discover(str(args["purpose"])))
        if name == "linguini_chain":
            steps = list(args.get("steps") or [])
            return _ok_text(ling.chain(steps, text=str(args.get("text", ""))))
        if name == "linguini_forge":
            result = ling.forge(
                str(args["need"]),
                name=args.get("name"),
                require_native=bool(args.get("require_native")),
                force_forge=bool(args.get("force")),
                persist=bool(args.get("persist", True)),
                template=str(args.get("template") or "auto"),
            )
            return _ok_text(result.to_dict() if hasattr(result, "to_dict") else result)
        if name == "linguini_create_native":
            fr = ling.create_native_tool(
                str(args["need"]),
                name=str(args["name"]),
                template=str(args.get("template") or "auto"),
                must_compose=args.get("steps"),
                persist=bool(args.get("persist", True)),
            )
            return _ok_text(fr.to_dict())
        if name == "linguini_wrap_chain":
            fr = ling.wrap_chain(
                list(args.get("steps") or []),
                name=str(args["name"]),
                need=args.get("need"),
                persist=bool(args.get("persist", True)),
            )
            return _ok_text(fr.to_dict())
        return _err_text(f"Unknown tool: {name}")
    except Exception as exc:  # noqa: BLE001 — surface to MCP client
        return _err_text(f"{type(exc).__name__}: {exc}")


def _respond(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _respond_error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def dispatch(ling: "Linguini", message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        from linguini import __version__ as pkg_version

        return _respond(
            msg_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": pkg_version},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _respond(msg_id, {})
    if method == "tools/list":
        return _respond(msg_id, {"tools": TOOLS})
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not tool_name:
            return _respond_error(msg_id, -32602, "missing tool name")
        return _respond(msg_id, handle_tool(ling, str(tool_name), arguments))
    if msg_id is None:
        return None
    return _respond_error(msg_id, -32601, f"Method not found: {method}")


def serve_stdio(root: Path | str = ".") -> int:
    from linguini.api import Linguini

    ling = Linguini(root=root)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            err = _respond_error(None, -32700, "Parse error")
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()
            continue
        response = dispatch(ling, message)
        if response is not None:
            sys.stdout.write(json.dumps(response, default=str) + "\n")
            sys.stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="linguini-mcp", description="Linguini MCP stdio server")
    p.add_argument("--root", default=".", help="Project root for native tools")
    args = p.parse_args(argv)
    return serve_stdio(Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
