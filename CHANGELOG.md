# Changelog

## 0.1.2

- Tutorial: [docs/TUTORIAL.md](docs/TUTORIAL.md) — forge and reuse novel tools
- Runnable examples under `examples/` (create, use, wrap-chain, lean-back vs forge, pipeline)
- Docs index: [docs/README.md](docs/README.md), [docs/EXAMPLES.md](docs/EXAMPLES.md)
- MCP discover: optional `LINGUINI_MCP_CATALOG` overlay + `catalog_source` on results

## 0.1.1

- `Linguini.create_native_tool` / `wrap_chain` — always forge novel natives; persist on green
- Novel codegen templates: `entity_hygiene`, `tokenize_hygiene`, `chain_wrap`, `lowercase_tokens`
- MCP stdio server (`linguini mcp` / `linguini-mcp`) with `linguini_create_native`
- CLI: `create`, `wrap-chain`, `forge --native`, `hygiene`
- Expanded NLP suite ops + CARAG/Netrin secondary hygiene stubs
- E2E tests proving create → persist → reload → run

## 0.1.0

- Purpose-first tool foundry: ground → lean-back/chain → forge → pytest loop → persist
- Strict sandbox (no network / disallowed imports by default)
- Soft NLP suite adapters + tooling library + native registry
- MCP discover fixture catalog + local chain planner
- CLI: `forge`, `tools`, `discover`, `chain`, `backends`
