# Tool forge / invent

Prefer the **inventor** path — see [INVENT.md](INVENT.md).

## Purpose contract

`ForgePurpose` carries `need`, `examples`, `invariants`, optional `must_compose`, and:

- `require_native=True` — never lean-back onto library aliases; invent a native
- `template` / skill id — maps to `invent/skills/*.yaml`

## Invent native tools

```python
ling = Linguini(root=".")
ir = ling.invent(
    "novel entity hygiene analyzer",
    name="entity_hygiene_v1",
    prefer_skill="entity_hygiene",
)
# → lint + pytest + persist under .linguini/native_tools/
```

CLI:

```powershell
python -m linguini invent --need "novel entity hygiene" --name my_op --skill entity_hygiene
python -m linguini wrap-chain --steps "nlp.tokenize,nlp.claim_hygiene" --name chain_op
```

MCP tools: `linguini_invent`, `linguini_create_native`, `linguini_wrap_chain`, `linguini_forge`.

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
