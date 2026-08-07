# Agents — Linguini

Invent and reuse **native tools** (MCP + libs + skills → lint/pytest → persist). Prefer lean-back compose; do not skip verify gates.

## Connect

1. `pip install -e ".[mcp]"` (or `.[dev,mcp]`)
2. MCP: `python -m linguini.mcp.server --root .` — Cursor: [`.cursor/mcp.json`](.cursor/mcp.json)
3. Skill: [`.cursor/skills/linguini/SKILL.md`](.cursor/skills/linguini/SKILL.md)
4. Guide: [docs/TUTORIAL.md](docs/TUTORIAL.md)

## Tools (MCP)

`linguini_invent`, `linguini_create_native`, `linguini_forge`, `linguini_tools_list`, `linguini_tools_run`, `linguini_discover`, `linguini_chain`, `linguini_wrap_chain`, `linguini_skills_list`, `linguini_libs_list`, `linguini_npm_list`, `linguini_backends`

## Loop

1. `linguini_invent` / `linguini_create_native` with a clear need  
2. Only trust `persisted` after green lint/pytest  
3. `linguini_tools_run` to exercise `native.*`  
4. Prefer reuse of existing natives over re-inventing  

## CLI

```powershell
python -m linguini invent --need "…" --name my_tool
python -m linguini tools run native.my_tool --text "…"
```
