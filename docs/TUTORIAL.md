# Tutorial: forge and reuse novel tools

This walkthrough takes you from a purpose to a **persisted native tool** you can run from Python, the CLI, or MCP.

Time: ~10 minutes. No GPU. Heuristic NLP backends work out of the box.

## 0. Install

```powershell
cd research/linguini
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Confirm:

```powershell
python -m linguini backends
python -m linguini tools list --layer nlp
```

## 1. Mental model

```
purpose  →  ground evidence
         →  lean-back / chain existing tools   (prefer this)
         →  forge novel native only on gap
         →  pytest loop in sandbox
         →  persist under .linguini/native_tools/
         →  reuse as native.<name>
```

| Mode | When | Result |
|------|------|--------|
| **chain** | An existing `nlp.*` / `builtin.*` / prior `native.*` already passes your examples | No new file written |
| **forge** | Gap remains, or you set `require_native` / call `create_native_tool` | New native after green tests |

## 2. Lean-back first (no forge)

```python
from linguini import Linguini, ForgePurpose, IOExample

ling = Linguini(root=".")
result = ling.fulfill(
    ForgePurpose(
        need="tokenize and lowercase text",
        examples=[
            IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})
        ],
        invariants=["output tokens are lowercase"],
    )
)
print(result.mode)   # "chain"
print(result.reason)
```

CLI equivalent:

```powershell
python -m linguini forge --need "tokenize and lowercase text"
# Often satisfies via lean-back; add --native to force a new tool
```

## 3. Create a novel native tool

Use `create_native_tool` when you want a **new** composite op (not a thin alias of `nlp.tokenize`).

```python
from linguini import Linguini, IOExample

ling = Linguini(root=".")
fr = ling.create_native_tool(
    "novel claim analyzer: entities + lemmas + causation hygiene",
    name="claim_analyzer",
    template="entity_hygiene",
    examples=[
        IOExample(
            input="Acme Corp grew 12%. Demand looks fine.",
            expected={"novel": True},
        )
    ],
    invariants=["output tokens are lowercase"],
)
assert fr.ok and fr.persisted
print(fr.native_name)  # native.claim_analyzer
```

What happened:

1. Codegen picked the `entity_hygiene` template (composite of suite ops).
2. Pytest was generated from your examples + invariants.
3. Sandbox static-scan ran; tests executed in a temp dir.
4. On green, source + tests + `registry.yaml` were written under `.linguini/native_tools/`.

CLI:

```powershell
python -m linguini create --need "novel claim analyzer" --name claim_analyzer --template entity_hygiene
```

Templates:

| Template | Output shape (high level) |
|----------|---------------------------|
| `entity_hygiene` | tokens, lemmas, entities, hygiene, topics, sentences, `novel: true` |
| `tokenize_hygiene` | tokens + hygiene composite |
| `lowercase_tokens` | tokens + lemmas |
| `chain_wrap` | ordered suite/tool steps → `chain` + `outputs` |
| `auto` | chooses from the need text / `require_native` |

## 4. Use the novel tool

```python
out = ling.run_tool(
    "native.claim_analyzer",
    text="Demand looks like last quarter so raise price",
)
print(out["entities"])
print(out["hygiene"])   # spurious_causation flag
print(out["novel"])     # True
```

CLI:

```powershell
python -m linguini tools list --layer native
python -m linguini tools run native.claim_analyzer --text "Acme Corp grew 12%."
```

After process restart, `Linguini(root=...)` reloads `registry.yaml` automatically — natives stay available.

## 5. Wrap a chain as one native

When a multi-step plan works, freeze it into a single tool:

```python
fr = ling.wrap_chain(
    ["nlp.lowercase_tokens", "nlp.claim_hygiene"],
    name="tok_then_hygiene",
)
out = ling.run_tool("native.tok_then_hygiene", text="Hello World")
print(out["chain"], out["final"])
```

```powershell
python -m linguini wrap-chain --steps "nlp.lowercase_tokens,nlp.claim_hygiene" --name tok_then_hygiene
```

You can also chain library ops **into** natives:

```python
ling.chain(["nlp.sentences", "native.claim_analyzer"], text="First. Second.")
```

## 6. Force forge vs lean-back

```python
# Always create a native even if nlp.lowercase_tokens would suffice
from linguini import ForgePurpose, IOExample

result = ling.fulfill(
    ForgePurpose(
        need="tokenize and lowercase text",
        examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
        name="my_lower",
        require_native=True,
        template="lowercase_tokens",
    )
)
assert result.mode == "forge"
```

Or:

```powershell
python -m linguini forge --need "tokenize and lowercase text" --name my_lower --native
```

## 7. MCP

Expose create/run over stdio:

```powershell
python -m linguini mcp
# or: linguini-mcp --root .
```

Tools include `linguini_create_native`, `linguini_wrap_chain`, `linguini_tools_run`, `linguini_forge`, `linguini_discover`, `linguini_chain`.

Point an MCP client at that command; call `linguini_create_native` with `need` + `name`, then `linguini_tools_run`.

## 8. Where files land

```
<root>/.linguini/native_tools/
  registry.yaml          # name → path, purpose_hash, created_at
  claim_analyzer.py      # run(text=...) implementation
  test_claim_analyzer.py # pytest that gated persist
```

Nothing is written if tests fail (`persisted=False`).

## 9. Run the packaged examples

```powershell
$env:PYTHONPATH = "src"
python examples/run_all.py
```

See [examples/README.md](../examples/README.md) and [EXAMPLES.md](EXAMPLES.md).

## 10. Next steps

- Read [TOOL_FORGE.md](TOOL_FORGE.md) for the purpose contract and test loop.
- Read [SANDBOX.md](SANDBOX.md) for what natives may not import/do.
- Read [MCP_CHAIN.md](MCP_CHAIN.md) for discover/chain (live registry in v0.2).
- Secondary hygiene: `python -m linguini hygiene carag --text "..."` / `netrin`.
