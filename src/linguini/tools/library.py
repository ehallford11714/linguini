"""Tooling library: nlp.* + builtin.* + native.* layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from linguini.suite.nlp import NLPSuite


@dataclass
class ToolSpec:
    name: str
    layer: str
    description: str = ""
    handler: Optional[Callable[..., Any]] = field(default=None, repr=False)
    path: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "layer": self.layer,
            "description": self.description,
            "path": self.path,
            "meta": dict(self.meta),
        }


class ToolLibrary:
    def __init__(self, root: Path | str, *, nlp: NLPSuite | None = None) -> None:
        self.root = Path(root)
        self.native_dir = self.root / ".linguini" / "native_tools"
        self.nlp = nlp or NLPSuite()
        self._tools: dict[str, ToolSpec] = {}
        self._register_builtins()
        self.reload_natives()

    def _register_builtins(self) -> None:
        for name in self.nlp.op_names():
            self._tools[name] = ToolSpec(
                name=name,
                layer="nlp",
                description=f"NLP suite op {name}",
                handler=lambda op=name, **kw: self.nlp.run(op, **kw),
            )
        self._tools["builtin.wisdom_check"] = ToolSpec(
            name="builtin.wisdom_check",
            layer="builtin",
            description="Reject similarity⇒causation justifications",
            handler=self._wisdom_check,
        )

    def _wisdom_check(self, text: str = "", justification: str = "", **_: Any) -> dict[str, Any]:
        blob = f"{text} {justification}".strip()
        h = self.nlp.claim_hygiene(blob)
        return {"ok": h["ok"], "spurious_causation": h["spurious_causation"], "detail": h}

    def reload_natives(self) -> None:
        # Drop previous natives
        for k in list(self._tools):
            if k.startswith("native."):
                del self._tools[k]
        reg = self.native_dir / "registry.yaml"
        if not reg.exists():
            return
        data = yaml.safe_load(reg.read_text(encoding="utf-8")) or {}
        for entry in data.get("tools") or []:
            name = entry.get("name")
            if not name:
                continue
            full = name if name.startswith("native.") else f"native.{name}"
            self._tools[full] = ToolSpec(
                name=full,
                layer="native",
                description=entry.get("description") or "",
                path=entry.get("path"),
                meta=dict(entry),
            )

    def list(self, layer: str | None = None) -> list[dict[str, Any]]:
        rows = [t.to_dict() for t in sorted(self._tools.values(), key=lambda x: x.name)]
        if layer:
            rows = [r for r in rows if r["layer"] == layer]
        return rows

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def run(self, name: str, **kwargs: Any) -> Any:
        tool = self.get(name)
        if tool.layer == "native":
            return self._run_native(tool, kwargs)
        if not tool.handler:
            raise RuntimeError(f"Tool has no handler: {name}")
        return tool.handler(**kwargs)

    def _run_native(self, tool: ToolSpec, kwargs: dict[str, Any]) -> Any:
        """Load native module run() under static scan — in-process for trusted persisted tools."""
        import os

        from linguini.sandbox.policy import SandboxPolicy
        from linguini.sandbox.runner import SandboxViolation, static_scan

        if not tool.path:
            raise RuntimeError(f"Native tool missing path: {tool.name}")
        path = Path(tool.path)
        if not path.is_absolute():
            path = self.root / path
        source = path.read_text(encoding="utf-8")
        violations = static_scan(source, SandboxPolicy())
        if violations:
            raise SandboxViolation("; ".join(violations))
        # Cross-runtime natives resolve npm modules under this root
        os.environ["LINGUINI_ROOT"] = str(self.root)
        ns: dict[str, Any] = {"__name__": tool.name}
        # Restricted exec of already-tested natives
        exec(compile(source, str(path), "exec"), ns, ns)  # noqa: S102 — gated by static_scan + prior pytest
        if "run" not in ns:
            raise RuntimeError(f"Native tool {tool.name} has no run()")
        return ns["run"](**kwargs)
