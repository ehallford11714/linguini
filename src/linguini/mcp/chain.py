"""Local tool chaining (v0.1) — remote MCP servers via allowlist later."""

from __future__ import annotations

from typing import Any

from linguini.tools.library import ToolLibrary


def run_chain(library: ToolLibrary, steps: list[str], *, text: str) -> dict[str, Any]:
    """Run ordered local tools; each output can feed next as text if str/dict."""
    outputs: list[Any] = []
    current: Any = text
    for step in steps:
        kwargs: dict[str, Any] = {"text": current if isinstance(current, str) else text, "input": text}
        if isinstance(current, dict):
            kwargs.update({k: v for k, v in current.items() if isinstance(v, (str, int, float, bool))})
        out = library.run(step, **kwargs)
        outputs.append({"tool": step, "output": out})
        current = out
    return {"ok": True, "steps": steps, "outputs": outputs, "final": current}
