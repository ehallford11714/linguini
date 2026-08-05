"""InventionPlan — frozen deterministic bounds for LLM-assisted codegen."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class PlanStep:
    kind: str  # nlp | lib | mcp | code
    ref: str
    package: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "ref": self.ref,
            "package": self.package,
            "meta": dict(self.meta),
        }


@dataclass
class InventionPlan:
    """Deterministic invention plan. bounds_hash freezes allowlists for LLM fill."""

    name: str
    need: str
    skill_id: str
    steps: list[PlanStep] = field(default_factory=list)
    allowed_imports: list[str] = field(default_factory=list)
    pip_deps: list[str] = field(default_factory=list)
    mcp_tools: list[str] = field(default_factory=list)
    template: str = "entity_hygiene"
    require_novel: bool = True
    expected_schema: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    discover: list[dict[str, Any]] = field(default_factory=list)
    bounds_hash: str = ""
    frozen: bool = False

    def freeze(self) -> "InventionPlan":
        payload = {
            "name": self.name,
            "need": self.need,
            "skill_id": self.skill_id,
            "steps": [s.to_dict() for s in self.steps],
            "allowed_imports": sorted(set(self.allowed_imports)),
            "pip_deps": sorted(set(self.pip_deps)),
            "mcp_tools": sorted(set(self.mcp_tools)),
            "template": self.template,
            "require_novel": self.require_novel,
        }
        blob = json.dumps(payload, sort_keys=True, default=str)
        self.bounds_hash = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
        self.allowed_imports = sorted(set(self.allowed_imports))
        self.pip_deps = sorted(set(self.pip_deps))
        self.mcp_tools = sorted(set(self.mcp_tools))
        self.frozen = True
        return self

    def assert_frozen(self) -> None:
        if not self.frozen or not self.bounds_hash:
            raise RuntimeError("InventionPlan must be freeze()d before LLM fill or codegen")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "need": self.need,
            "skill_id": self.skill_id,
            "steps": [s.to_dict() for s in self.steps],
            "allowed_imports": list(self.allowed_imports),
            "pip_deps": list(self.pip_deps),
            "mcp_tools": list(self.mcp_tools),
            "template": self.template,
            "require_novel": self.require_novel,
            "expected_schema": dict(self.expected_schema),
            "evidence": list(self.evidence),
            "discover": list(self.discover),
            "bounds_hash": self.bounds_hash,
            "frozen": self.frozen,
        }


@dataclass
class InventionBrief:
    """Optional extras on a purpose for invention."""

    allowed_mcp: list[str] = field(default_factory=list)
    allowed_libs: list[str] = field(default_factory=list)
    prefer_skill: Optional[str] = None
    use_llm: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
