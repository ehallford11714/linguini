# MCP discovery & chaining

## v0.1

- Offline fixture catalog of purpose-aligned servers (Fetch, Memory, Sequential Thinking, Filesystem, GitHub, CodeForge)  
- `linguini discover --purpose "…"` ranks by keyword/tag overlap  
- `linguini chain` runs **local** tool steps  

## v0.2 (planned)

- Live queries against [MCP Registry](https://registry.modelcontextprotocol.io/)  
- Multi-server chains behind `allow_mcp_servers` allowlist  

Remote servers are never auto-installed without explicit allowlist consent.
