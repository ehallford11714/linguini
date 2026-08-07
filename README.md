# Linguini

**Tool inventor** — compose MCP servers, allowlisted open-source libraries, and coding skills into **novel native tools**. Lean-back first; LLM fill only inside deterministic bounds; lint + pytest before any persist.

```
purpose → discover (MCP + libs + skills)
       → lean-back / compose existing adapters
       → invent plan (frozen bounds)
       → [optional LLM fill within bounds]
       → lint verifier → pytest sandbox
       → persist native only on green
       → reuse via CLI / MCP / chain
```

## For agents (MCP)

**Start here:** [AGENTS.md](AGENTS.md)

```powershell
pip install -e ".[mcp]"
python -m linguini.mcp.server --root .
```

Cursor: [`.cursor/mcp.json`](.cursor/mcp.json) · skill: [`.cursor/skills/linguini/SKILL.md`](.cursor/skills/linguini/SKILL.md)

## Install

```powershell
cd research/linguini
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

## Invent a novel tool

```python
from linguini import Linguini

ling = Linguini(root=".")
ir = ling.invent(
    "novel entity hygiene analyzer for claims",
    name="claim_analyzer",
    prefer_skill="entity_hygiene",  # or omit to auto-score skills
)
assert ir.persisted
print(ling.run_tool("native.claim_analyzer", text="Acme Corp grew 12%."))
```

```powershell
python -m linguini invent --need "chain mcp fetch and memory with hygiene" --name mcp_chain --skill mcp_chain_wrap
python -m linguini skills list
python -m linguini libs list
python -m linguini tools run native.mcp_chain --text "Ground this claim"
```

Cross-runtime (npm + Python) and open installs:

```powershell
python -m linguini npm list
python -m linguini invent --need "markdown npm parse hygiene" --name md_op --skill md_npm_hygiene
# Beyond curated catalogs (still sanitized + isolated + verify-always):
python -m linguini invent --need "..." --name x --skill entity_hygiene --open-pip --open-npm
```

Bounded LLM fill (optional; needs `LINGUINI_LLM_API_KEY` / `OPENAI_API_KEY`):

```powershell
python -m linguini invent --need "..." --name my_op --llm
```

## Chain mechanism

| Stage | What |
|-------|------|
| **Purpose** | `ForgePurpose` / invent need |
| **Discover** | MCP catalog (tool schemas) + lib allowlist |
| **Skills** | Deterministic recipes under `invent/skills/` |
| **Plan** | Frozen `InventionPlan` (LLM cannot expand allowlist) |
| **Hooks** | lint → pytest → persist gates |
| **Reuse** | `native.*` via CLI / MCP / `chain` |

## Tutorial & examples

- **[Tutorial](docs/TUTORIAL.md)** — invent, verify, reuse + skill catalog (NLP / MCP / pip / npm)
- **[Examples](docs/EXAMPLES.md)** · [`examples/`](examples/)
- **[INVENT.md](docs/INVENT.md)** — inventor architecture

```powershell
$env:PYTHONPATH = "src"
python examples/run_all.py
```

## Docs

| Doc | Topic |
|-----|--------|
| [docs/TUTORIAL.md](docs/TUTORIAL.md) | Walkthrough |
| [docs/INVENT.md](docs/INVENT.md) | Inventor + bounds + hooks |
| [docs/TOOL_FORGE.md](docs/TOOL_FORGE.md) | Purpose / persist loop |
| [docs/MCP_CHAIN.md](docs/MCP_CHAIN.md) | Discover + MCP |
| [docs/SANDBOX.md](docs/SANDBOX.md) | Threat model |

## License

MIT
