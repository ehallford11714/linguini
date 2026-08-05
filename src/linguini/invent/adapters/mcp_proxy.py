"""Local/fixture MCP tool proxy — calls allowlisted tools (stdio later)."""

from __future__ import annotations

from typing import Any

from linguini.mcp.discover import load_catalog


def list_mcp_tool_schemas() -> list[dict[str, Any]]:
    catalog, source = load_catalog()
    tools: list[dict[str, Any]] = []
    for srv in catalog.get("servers") or []:
        sid = srv.get("id")
        for tool in srv.get("tools") or []:
            row = dict(tool)
            row["server"] = sid
            row["full_name"] = f"{sid}.{tool.get('name')}"
            row["catalog_source"] = source
            tools.append(row)
    return tools


def call_mcp_tool(
    tool_id: str,
    *,
    arguments: dict[str, Any] | None = None,
    allow_mcp_servers: list[str] | None = None,
) -> dict[str, Any]:
    """
    Invoke an MCP tool by id (`server.tool`).

    v0.2: fixture/local stub — returns structured mock grounded in catalog schema.
    Real stdio clients land when allow_mcp_servers opts into live servers.
    """
    arguments = arguments or {}
    server = tool_id.split(".")[0] if "." in tool_id else tool_id
    allow = allow_mcp_servers or []
    # Empty allowlist = fixture stubs only (safe default)
    if allow and server not in allow and tool_id not in allow:
        raise PermissionError(f"MCP server/tool not allowlisted: {tool_id}")

    schemas = {t["full_name"]: t for t in list_mcp_tool_schemas()}
    # also allow bare tool names unique match
    if tool_id not in schemas:
        matches = [t for t in schemas.values() if t.get("name") == tool_id or t["full_name"].endswith(f".{tool_id}")]
        if len(matches) == 1:
            schema = matches[0]
            tool_id = schema["full_name"]
        else:
            # still stub unknown for compose demos if server is in catalog
            schema = {"server": server, "name": tool_id, "description": "stub"}
    else:
        schema = schemas[tool_id]

    text = str(arguments.get("text") or arguments.get("url") or arguments.get("query") or "")
    return {
        "ok": True,
        "tool": tool_id,
        "server": schema.get("server", server),
        "stub": True,
        "input": arguments,
        "output": {
            "text": text,
            "note": f"fixture stub for {tool_id}",
            "schema": {k: schema.get(k) for k in ("name", "description", "inputSchema") if k in schema},
        },
        "novel_material": True,
    }
