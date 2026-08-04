# Examples catalog

Runnable scripts live in [`examples/`](../examples/). They write natives under `examples/_workspace/` (gitignored except `.gitkeep`).

## Create novel tools

| Example | API | Persists |
|---------|-----|----------|
| `01_create_novel_tool.py` | `create_native_tool(..., template="entity_hygiene")` | `native.claim_analyzer` |
| `03_wrap_chain_as_native.py` | `wrap_chain([...])` | `native.tok_then_hygiene` |
| `04_leanback_vs_forge.py` | `fulfill(... require_native=True)` | `native.forced_lower_tokens` |
| `05_create_and_reuse_pipeline.py` | two `create_native_tool` calls | `native.pipeline_*` |

## Use novel tools

| Example | How |
|---------|-----|
| `02_use_novel_tool.py` | `run_tool("native.claim_analyzer", text=...)` on several claims |
| `03_wrap_chain_as_native.py` | run wrapped chain; compare to ad-hoc `chain` |
| `05_create_and_reuse_pipeline.py` | list natives → run → `chain(nlp → native)` |

## Patterns (copy/paste)

### Create

```python
from linguini import Linguini

ling = Linguini(root=".")
fr = ling.create_native_tool(
    "novel entity hygiene analyzer",
    name="my_analyzer",
    template="entity_hygiene",
)
assert fr.persisted
```

### Use

```python
out = ling.run_tool("native.my_analyzer", text="Acme Corp grew 12%.")
assert out["novel"] is True
```

### Wrap chain

```python
ling.wrap_chain(
    ["nlp.lowercase_tokens", "nlp.claim_hygiene"],
    name="tok_hygiene",
)
ling.run_tool("native.tok_hygiene", text="Hello")
```

### CLI

```powershell
python -m linguini create --need "novel entity hygiene" --name my_analyzer
python -m linguini tools run native.my_analyzer --text "Acme Corp grew 12%."
```

Full narrative: [TUTORIAL.md](TUTORIAL.md).
