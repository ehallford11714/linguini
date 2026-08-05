# Tool inventor

Linguini’s main focus: **invent novel tools** by combining MCP servers, allowlisted libraries, and skill recipes — not thin NLP aliases.

## Pipeline

```
purpose → discover → lean-back/compose
       → InventionPlan.freeze()     # bounds hash locked
       → TemplateBackend or LLM fill
       → lint (AST / imports / MCP refs)
       → allowlisted pip → forge_venv
       → pytest
       → persist native.*
```

## Skills (deterministic recipes)

Listed with `linguini skills list`. Shipped skills:

| Skill | Combines |
|-------|----------|
| `entity_hygiene` | NLP entity + hygiene composite |
| `tokenize_hygiene` | tokens + claim hygiene |
| `lowercase_tokens` | tokens + lemmas |
| `html_ground_parse` | BeautifulSoup + NLP + `fetch.fetch` stub |
| `mcp_chain_wrap` | `fetch.fetch` + `memory.search` stubs + hygiene |

Add YAML under `src/linguini/invent/skills/`.

## Pip + npm (cross-runtime)

| CLI | Catalog | Install root |
|-----|---------|--------------|
| `linguini libs list` | `invent/lib_catalog.yaml` | `.linguini/forge_venv/` |
| `linguini npm list` | `invent/npm_catalog.yaml` | `.linguini/forge_node/` |

**Default:** only curated catalog packages.  
**Open mode:** `--open-pip` / `--open-npm` (or `SandboxPolicy.allow_open_pip/npm`) installs beyond the catalog into the same isolated dirs. Specs are name-sanitized (no shell metacharacters). Lint + pytest still gate persist.

Runtime-network packages (`network: true` in catalog, e.g. `httpx`) still need `allow_network`.

Cross-runtime bridge: `linguini.invent.adapters.node_proxy` (e.g. skill `md_npm_hygiene` = npm `marked` + Python hygiene).

## LLM bounds

With `--llm` / `use_llm=True`:

- Input = purpose + **frozen** InventionPlan JSON
- Output = JSON `{source, tests}` only
- Lint must pass; one repair inside the same plan; then refuse
- LLM cannot add imports, MCP tools, or pip deps outside the plan

Default offline path uses `TemplateBackend` (no API).

## Hooks

1. `pre_invent` — grounding/discover evidence  
2. `post_plan` — freeze bounds hash  
3. `post_codegen` — **lint verifier**  
4. `post_tests` — pytest gate  
5. `post_persist` — reload library  

## MCP proxy

`linguini.invent.adapters.mcp_proxy.call_mcp_tool` returns fixture stubs for catalog tool schemas until `allow_mcp_servers` opts into live stdio servers.
