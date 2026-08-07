---
name: linguini
description: >-
  Invent novel native tools from MCP servers, allowlisted libraries, and skills
  with lint+pytest gates. Use when the user needs a new reusable tool, forge a
  native, wrap a chain, or run linguini_* MCP tools. Prefer invent-once → reuse.
---

# Linguini

## Connect

`.cursor/mcp.json` → `python -m linguini.mcp.server --root .`  
Install: `pip install -e ".[mcp]"`

## Loop

1. `linguini_skills_list` / `linguini_discover` if unsure  
2. `linguini_invent` or `linguini_create_native`  
3. Confirm persisted; then `linguini_tools_run`  
4. Never bypass sandbox verify  

See `AGENTS.md`.
