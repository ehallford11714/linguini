# Tool forge

## Purpose contract

`ForgePurpose` carries `need`, `examples`, `invariants`, optional `must_compose`, and:

- `require_native=True` — never lean-back onto library aliases; always forge a native
- `template` — `auto` | `entity_hygiene` | `tokenize_hygiene` | `lowercase_tokens` | `chain_wrap`

## Create native tools

Primary APIs (always forge + testloop; persist only on green):

```python
ling = Linguini(root=".")
fr = ling.create_native_tool(
    "novel entity hygiene analyzer",
    name="entity_hygiene_v1",
    template="entity_hygiene",
)
# → native.entity_hygiene_v1 under .linguini/native_tools/

fr = ling.wrap_chain(
    ["nlp.lowercase_tokens", "nlp.claim_hygiene"],
    name="tok_hygiene_chain",
)
```

CLI:

```powershell
python -m linguini create --need "novel entity hygiene" --name my_op
python -m linguini forge --need "..." --name my_op --native
python -m linguini wrap-chain --steps "nlp.tokenize,nlp.claim_hygiene" --name chain_op
```

MCP tools: `linguini_create_native`, `linguini_wrap_chain`, `linguini_forge`.

## Loop

1. Generate implementation + `pytest` from examples  
2. Static sandbox scan  
3. Run pytest in a temp dir  
4. Repair up to `max_repairs`  
5. **Persist only if green**

## Lean-back

`Linguini.fulfill` tries existing `nlp.*` / `builtin.*` tools first. If examples pass, mode=`chain` and nothing is forged — unless `require_native=True`.

## Tutorial & examples

- Walkthrough: [TUTORIAL.md](TUTORIAL.md)
- Runnable create/use scripts: [EXAMPLES.md](EXAMPLES.md) · [`examples/`](../examples/)
