# MCP discovery & chaining

## v0.1 / 0.1.x

- Offline fixture catalog of purpose-aligned servers (Fetch, Memory, Sequential Thinking, Filesystem, GitHub, CodeForge)  
- `linguini discover --purpose "…"` ranks by keyword/tag overlap  
- Optional local overlay: set `LINGUINI_MCP_CATALOG` to a JSON file with a `servers` array (merged by `id`)  
- Results include `catalog_source`: `fixture` or `merged`  
- `linguini chain` runs **local** tool steps  
- Stdio MCP server: `linguini mcp` / `linguini-mcp` exposing forge, `linguini_create_native`, tools, chain, discover  

## v0.2

- Catalog entries include **tool schemas** (`tools[]` with `inputSchema`)
- Fixture/local proxy: `linguini.invent.adapters.mcp_proxy.call_mcp_tool`
- Invention skills can compose MCP tool ids into natives (`mcp_chain_wrap`)
- Live registry client still optional; overlay via `LINGUINI_MCP_CATALOG`
- Multi-server live chains behind `allow_mcp_servers` allowlist (opt-in)

Remote servers are never auto-installed without explicit allowlist consent.
