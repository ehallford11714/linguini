# Tool forge

## Purpose contract

`ForgePurpose` carries `need`, `examples`, `invariants`, and optional `must_compose`.

## Loop

1. Generate implementation + `pytest` from examples  
2. Static sandbox scan  
3. Run pytest in a temp dir  
4. Repair up to `max_repairs`  
5. **Persist only if green**

## Lean-back

`Linguini.fulfill` tries existing `nlp.*` / `builtin.*` tools first. If examples pass, mode=`chain` and nothing is forged.
