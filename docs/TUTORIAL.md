# Tutorial: invent and reuse novel tools

~10 minutes. Heuristic NLP + fixture MCP stubs work offline.

## 0. Install

```powershell
cd research/linguini
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## 1. Mental model

Linguini **invents** tools when lean-back cannot satisfy a purpose:

1. Score **skills** (recipes) + MCP + allowlisted libs  
2. Freeze an **InventionPlan** (deterministic bounds)  
3. Fill code (template stitch, or bounded LLM)  
4. **Lint** then **pytest** — persist only on green  
5. Reuse as `native.<name>`

## 2. Lean-back first

```python
from linguini import Linguini, ForgePurpose, IOExample

ling = Linguini(root=".")
r = ling.fulfill(
    ForgePurpose(
        need="tokenize and lowercase text",
        examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
    )
)
print(r.mode)  # "chain" — no invent
```

## 3. Invent via skill

```python
ir = ling.invent(
    "novel entity hygiene analyzer for claims",
    name="claim_analyzer",
    prefer_skill="entity_hygiene",
)
assert ir.ok and ir.persisted
print(ir.plan.bounds_hash)
print(ling.run_tool("native.claim_analyzer", text="Acme Corp grew 12%."))
```

CLI:

```powershell
python -m linguini invent --need "novel entity hygiene" --name claim_analyzer --skill entity_hygiene
python -m linguini tools run native.claim_analyzer --text "Acme Corp grew 12%."
```

## 4. Invent across MCP stubs

```powershell
python -m linguini invent --need "chain mcp fetch memory hygiene" --name mcp_combo --skill mcp_chain_wrap
python -m linguini tools run native.mcp_combo --text "Ground Acme"
```

The native calls fixture MCP proxies (`fetch.fetch`, `memory.search`) then claim hygiene — one reusable tool.

## 5. Invent with an allowlisted library

```powershell
python -m linguini invent --need "html parse grounding docs entities" --name html_op --skill html_ground_parse
```

This may `pip install beautifulsoup4` into `.linguini/forge_venv/` (allowlisted only), then lint + pytest, then persist.

## 6. Optional LLM fill

```powershell
$env:LINGUINI_LLM_API_KEY = "..."
python -m linguini invent --need "..." --name llm_op --skill entity_hygiene --llm
```

The LLM only fills glue inside the frozen plan; lint rejects out-of-bounds imports.

## 7. Inspect catalogs

```powershell
python -m linguini skills list
python -m linguini libs list
python -m linguini discover --purpose "fetch docs entities"
```

## 8. Packaged examples

```powershell
$env:PYTHONPATH = "src"
python examples/run_all.py
```

See [EXAMPLES.md](EXAMPLES.md) and [INVENT.md](INVENT.md).
