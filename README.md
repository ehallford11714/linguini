# Linguini

**NLP suite + tooling library that forges native novel tools ad hoc — grounded, verifiable, lean-back first.**

```
ground purpose → discover / lean-back chain existing tools
             → forge only if gap remains
             → unit-test loop (persist only on green)
             → save native tools for future MCP/CLI use
```

## Install

```powershell
cd research/linguini
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

## Tutorial & examples

- **[Tutorial: forge and reuse novel tools](docs/TUTORIAL.md)** — start here
- **[Examples catalog](docs/EXAMPLES.md)** · runnable scripts in [`examples/`](examples/)

```powershell
$env:PYTHONPATH = "src"
python examples/run_all.py
```

## Create a native tool

```python
from linguini import Linguini

ling = Linguini(root=".")
fr = ling.create_native_tool(
    "novel entity hygiene analyzer for claims",
    name="entity_hygiene_v1",
)
assert fr.persisted
print(ling.run_tool("native.entity_hygiene_v1", text="Acme Corp grew 12%."))
```

```powershell
python -m linguini create --need "novel entity hygiene" --name entity_hygiene_v1
python -m linguini tools run native.entity_hygiene_v1 --text "Acme Corp grew 12%."
python -m linguini wrap-chain --steps "nlp.lowercase_tokens,nlp.claim_hygiene" --name tok_hygiene
```

MCP stdio server (also `linguini-mcp`):

```powershell
python -m linguini mcp
```

## Lean-back first

```python
from linguini import Linguini, ForgePurpose, IOExample

ling = Linguini(root=".")
result = ling.fulfill(
    ForgePurpose(
        need="tokenize and lowercase text",
        examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
    )
)
print(result.mode)  # "chain" when existing tools suffice; "forge" on gap / require_native
```

## Operating principles

| Principle | Meaning |
|-----------|---------|
| **Grounding** | Forge/chain steps cite evidence (examples, NLP spans, docs) |
| **Verifiable** | Persist natives only after green pytest |
| **Lean-back** | Prefer chaining existing NLP/MCP tools before creating new ones |
| **MCP chaining** | Compose multi-server tools; natives may wrap verified chains |

## Docs

| Doc | Topic |
|-----|--------|
| [docs/TUTORIAL.md](docs/TUTORIAL.md) | Forge & reuse walkthrough |
| [docs/EXAMPLES.md](docs/EXAMPLES.md) | Example scripts |
| [docs/PURPOSE.md](docs/PURPOSE.md) | Why Linguini exists |
| [docs/TOOL_FORGE.md](docs/TOOL_FORGE.md) | Purpose-driven forge |
| [docs/SANDBOX.md](docs/SANDBOX.md) | Threat model |
| [docs/MCP_CHAIN.md](docs/MCP_CHAIN.md) | Discovery + chaining |
| [docs/README.md](docs/README.md) | Docs index |

Secondary hygiene helpers: `linguini hygiene carag|netrin`.

## License

MIT
