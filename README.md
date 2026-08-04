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

## Quick start

```python
from linguini import Linguini, ForgePurpose, IOExample

ling = Linguini(root=".")

# Lean-back: use existing NLP tools when they already satisfy the purpose
result = ling.fulfill(
    ForgePurpose(
        need="tokenize and lowercase text",
        examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
        invariants=["output tokens are lowercase"],
    )
)
print(result.mode)  # "chain" or "forge"
print(result.evidence)

# List tooling layers
print(ling.tools.list())
```

```powershell
python -m linguini backends
python -m linguini tools list
python -m linguini discover --purpose "fetch docs and extract entities"
python -m linguini forge --need "compose tokenize + claim_hygiene" --name hygiene_tokens
```

## Operating principles

| Principle | Meaning |
|-----------|---------|
| **Grounding** | Forge/chain steps cite evidence (examples, NLP spans, docs) |
| **Verifiable** | Persist natives only after green pytest |
| **Lean-back** | Prefer chaining existing NLP/MCP tools before creating new ones |
| **MCP chaining** | Compose multi-server tools; natives may wrap verified chains |

## Docs

- [docs/PURPOSE.md](docs/PURPOSE.md) — why Linguini exists
- [docs/TOOL_FORGE.md](docs/TOOL_FORGE.md) — purpose-driven forge + test loop
- [docs/SANDBOX.md](docs/SANDBOX.md) — threat model
- [docs/MCP_CHAIN.md](docs/MCP_CHAIN.md) — discovery + chaining

Hygiene / advanced (secondary): CARAG dual-band context and Netrin-style routing may land in later releases; they are not the product headline.

## License

MIT
