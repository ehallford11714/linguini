# Changelog

## 0.2.1

- Expanded pip catalog + curated **npm** catalog for cross-runtime invention
- `npm install` into `.linguini/forge_node/`; `node_proxy` adapter for natives
- Open install flags: `--open-pip` / `--open-npm` (sanitized specs, isolated envs, verify-always)
- Skill `md_npm_hygiene` — npm `marked` + Python entity hygiene
- CLI: `linguini npm list`

## 0.2.0

- **Tool inventor** is the product focus: MCP + allowlisted libs + skills → novel natives
- `linguini invent` / `Linguini.invent` — compose → lint → pytest → persist
- Skills catalog (`invent/skills/`), lib allowlist (`lib_catalog.yaml`), lifecycle hooks
- Lint-like AST verifier before pytest; frozen `InventionPlan` bounds for LLM fill
- Allowlisted pip into `.linguini/forge_venv/`
- MCP catalog tool schemas + local fixture proxy (`call_mcp_tool`)
- Optional bounded LLM backend (`--llm` / `LINGUINI_LLM_API_KEY`)
- CLI: `skills list`, `libs list`; MCP: `linguini_invent`, `linguini_skills_list`
- Docs: INVENT.md, updated tutorial/examples

## 0.1.2

- Tutorial + runnable examples for create/use of novel natives
- MCP discover catalog overlay via `LINGUINI_MCP_CATALOG`

## 0.1.1

- `create_native_tool` / `wrap_chain`, novel templates, MCP stdio server

## 0.1.0

- Purpose-first foundry scaffold: ground → lean-back → forge → persist
