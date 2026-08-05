# Tutorial: invent and reuse novel tools

Linguini’s main focus is **generating novel tools** from skills that compose MCP servers, pip packages, npm packages, and NLP. Lean-back first; invent on gap; lint + pytest before persist.

## 0. Install

```powershell
cd research/linguini
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
# Optional for cross-runtime skills:
# node + npm on PATH
```

```powershell
python -m linguini skills list
python -m linguini libs list
python -m linguini npm list
```

## 1. Mental model

```
purpose → discover (MCP + pip + npm + skills)
       → lean-back if an existing tool already fits
       → invent: freeze InventionPlan → fill → lint → pytest → persist
       → reuse native.<name> in CLI / MCP / chain
```

## 2. Lean-back first (no invent)

```python
from linguini import Linguini, ForgePurpose, IOExample

ling = Linguini(root=".")
r = ling.fulfill(
    ForgePurpose(
        need="tokenize and lowercase text",
        examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
    )
)
print(r.mode)  # "chain"
```

## 3. Skill catalog — what can be generated

Run `python -m linguini skills list`. Each skill is a **recipe** Linguini can invent into a persisted `native.*` tool.

### Core NLP composites (no extra install)

| Skill | What the native does | Invent |
|-------|----------------------|--------|
| `entity_hygiene` | Entities + lemmas + claim hygiene + topics | `--skill entity_hygiene` |
| `tokenize_hygiene` | Lowercase tokens + spurious-causation hygiene | `--skill tokenize_hygiene` |
| `lowercase_tokens` | Tokens + lemmas as a named novel op | `--skill lowercase_tokens` |

```powershell
python -m linguini invent --need "novel entity hygiene analyzer" --name claim_analyzer --skill entity_hygiene
python -m linguini tools run native.claim_analyzer --text "Acme Corp grew 12%."
```

### MCP composition (fixture stubs offline; live later via allowlist)

| Skill | Combines | Invent |
|-------|----------|--------|
| `mcp_chain_wrap` | `fetch.fetch` → `memory.search` → hygiene | `--skill mcp_chain_wrap` |
| `repo_ground_pack` | `github.search_code` + `memory.search` + wisdom | `--skill repo_ground_pack` |
| `reflect_hygiene` | `sequential-thinking.think` → hygiene + posture | `--skill reflect_hygiene` |

```powershell
python -m linguini invent --need "chain mcp fetch memory hygiene" --name claim_grounder --skill mcp_chain_wrap
python -m linguini invent --need "github code grounding wisdom" --name repo_pack --skill repo_ground_pack
python -m linguini invent --need "reflect then hygiene gate" --name reflect_gate --skill reflect_hygiene
```

**Walkthrough — `repo_ground_pack`:** invent → run with a bugfix query → get stub GitHub + memory payloads, extracted entities, and `wisdom.ok` on the justification. Chain it before any execute step.

### Pip library composites (install into `.linguini/forge_venv/`)

| Skill | Pip deps | Capability |
|-------|----------|------------|
| `html_ground_parse` | `beautifulsoup4` | HTML → text + entities + fetch stub |
| `yaml_config_hygiene` | `pyyaml` | YAML config → hygiene on values |
| `bleach_sanitize_analyze` | `bleach` | Strip HTML → analyze |
| `jsonschema_claim_gate` | `jsonschema` | Validate claim JSON → hygiene gate |
| `networkx_entity_graph` | `networkx` | Entity co-occurrence graph |
| `date_aware_claims` | `python-dateutil` | Date spans + entity/claim hygiene |
| `spec_distill` | `mistune` | Markdown spec → checklist + topics + entities |

```powershell
python -m linguini invent --need "yaml config hygiene" --name yaml_gate --skill yaml_config_hygiene
python -m linguini tools run native.yaml_gate --text "claim: Demand looks like growth so buy`naction: expand"

python -m linguini invent --need "entity graph networkx" --name ent_graph --skill networkx_entity_graph
python -m linguini tools run native.ent_graph --text "Acme Corp partnered with Globex Inc in New York."

python -m linguini invent --need "distill markdown spec checklist" --name spec_op --skill spec_distill
```

**Walkthrough — `jsonschema_claim_gate`:** invent → run JSON `{"claim":"...","action":"..."}` → `valid` from schema + `hygiene` / `ok` combined gate. Use as a pre-action tool in agents.

### npm + Python cross-runtime (needs Node/npm on PATH)

| Skill | npm deps | Capability |
|-------|----------|------------|
| `md_npm_hygiene` | `marked` | Markdown → text → entity hygiene |
| `cheerio_npm_html` | `cheerio` | HTML DOM text + links → hygiene |
| `turndown_html_md` | `turndown` | HTML → markdown → hygiene |

```powershell
python -m linguini invent --need "markdown npm parse hygiene" --name md_op --skill md_npm_hygiene
python -m linguini invent --need "cheerio html extract entities" --name html_npm --skill cheerio_npm_html
python -m linguini invent --need "turndown html to markdown hygiene" --name td_op --skill turndown_html_md
```

**Walkthrough — `cheerio_npm_html`:** invent installs `cheerio` under `.linguini/forge_node/` → native calls `node_proxy.cheerio_to_text` → Python hygiene → returns `links`, `entities`, `novel: true`.

### Open installs (beyond curated catalogs)

Still name-sanitized, isolated dirs, lint + pytest before persist:

```powershell
python -m linguini invent --need "..." --name x --skill entity_hygiene --open-pip --open-npm
```

Add packages to a custom skill YAML under `src/linguini/invent/skills/`, or extend catalogs.

## 4. End-to-end invent → use → chain

```python
from linguini import Linguini

ling = Linguini(root=".")
ling.invent("reflect then hygiene", name="reflect_gate", prefer_skill="reflect_hygiene")
ling.invent("entity graph", name="ent_graph", prefer_skill="networkx_entity_graph")

out = ling.chain(
    ["native.reflect_gate", "native.ent_graph"],
    text="On Jan 15, 2024 Acme Corp partnered with Globex. Demand looks like growth so expand.",
)
print(out["steps"], out["final"].get("nodes") if isinstance(out["final"], dict) else out["final"])
```

## 5. Optional bounded LLM fill

```powershell
$env:LINGUINI_LLM_API_KEY = "..."
python -m linguini invent --need "..." --name llm_op --skill spec_distill --llm
```

LLM may only fill glue inside the frozen plan (imports / MCP / pip / npm bounds). Lint rejects violations.

## 6. Authoring a new skill

1. Add `src/linguini/invent/skills/<id>.yaml` with `compose_steps`, `pip_deps` / `npm_deps` / `mcp_tools`, `template`, `example_tests`.
2. Add a matching template in `invent/codegen.py` (or rely on `--llm` fill inside bounds).
3. Ensure packages appear in `lib_catalog.yaml` / `npm_catalog.yaml` (or use `--open-pip` / `--open-npm`).
4. Invent:

```powershell
python -m linguini invent --need "..." --name my_op --skill <id>
```

## 7. Packaged examples

```powershell
$env:PYTHONPATH = "src"
python examples/run_all.py
```

See [INVENT.md](INVENT.md), [EXAMPLES.md](EXAMPLES.md), [MCP_CHAIN.md](MCP_CHAIN.md).
