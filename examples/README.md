# Linguini examples

Runnable scripts that **create** novel native tools, then **use** them.

| Script | What it shows |
|--------|----------------|
| [`01_create_novel_tool.py`](01_create_novel_tool.py) | Forge + persist `native.claim_analyzer` |
| [`02_use_novel_tool.py`](02_use_novel_tool.py) | Reload registry and run the native |
| [`03_wrap_chain_as_native.py`](03_wrap_chain_as_native.py) | Wrap an NLP chain into one native |
| [`04_leanback_vs_forge.py`](04_leanback_vs_forge.py) | Lean-back vs `require_native` forge |
| [`05_create_and_reuse_pipeline.py`](05_create_and_reuse_pipeline.py) | Full create → list → run → chain pipeline |
| [`06_invent_mcp_and_lib.py`](06_invent_mcp_and_lib.py) | Invent MCP-chain skill native |
| [`run_all.py`](run_all.py) | Run every example in order |

Natives are written under `examples/_workspace/.linguini/native_tools/` (gitignored).

## Run

From the repo root:

```powershell
$env:PYTHONPATH = "src"
python examples/run_all.py
```

Or one at a time:

```powershell
$env:PYTHONPATH = "src"
python examples/01_create_novel_tool.py
python examples/02_use_novel_tool.py
```

See also: [docs/TUTORIAL.md](../docs/TUTORIAL.md).
