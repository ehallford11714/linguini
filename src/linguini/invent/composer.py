"""Deterministic composer — score skills + MCP + libs → InventionPlan (no LLM)."""

from __future__ import annotations

from typing import Any, Optional

from linguini.forge.purpose import ForgePurpose
from linguini.invent.catalogs import lib_by_name, list_libs, list_npm, load_skills, npm_by_name, skill_by_id
from linguini.invent.plan import InventionBrief, InventionPlan, PlanStep
from linguini.mcp.discover import discover_for_purpose


def _tokens(text: str) -> set[str]:
    return {t for t in text.lower().replace("/", " ").replace("-", " ").split() if len(t) > 2}


def score_skill(skill: dict[str, Any], purpose: ForgePurpose) -> int:
    tags = set(skill.get("purpose_tags") or [])
    need_toks = _tokens(purpose.need)
    score = sum(2 for t in tags if t in need_toks)
    score += sum(1 for t in need_toks if t in (skill.get("description") or "").lower())
    if purpose.template and purpose.template == skill.get("template"):
        score += 5
    if purpose.must_compose:
        refs = {s.get("ref") for s in (skill.get("compose_steps") or [])}
        score += 3 * len(set(purpose.must_compose) & refs)
    return score


def compose_plan(
    purpose: ForgePurpose,
    *,
    name: str,
    brief: InventionBrief | None = None,
    discover: list[dict[str, Any]] | None = None,
) -> InventionPlan:
    """Build a frozen InventionPlan from the best matching skill (+ discover evidence)."""
    brief = brief or InventionBrief()
    discovered = discover if discover is not None else discover_for_purpose(purpose)

    skill: Optional[dict[str, Any]] = None
    if brief.prefer_skill:
        skill = skill_by_id(brief.prefer_skill)
    if skill is None and purpose.template and purpose.template != "auto":
        skill = skill_by_id(purpose.template)
    if skill is None:
        ranked = sorted(load_skills(), key=lambda s: -score_skill(s, purpose))
        skill = ranked[0] if ranked and score_skill(ranked[0], purpose) > 0 else skill_by_id("entity_hygiene")
    if skill is None:
        skill = {
            "id": "entity_hygiene",
            "compose_steps": [{"kind": "nlp", "ref": "nlp.compose_entity_hygiene"}],
            "allowed_imports": ["linguini", "linguini.suite.nlp"],
            "pip_deps": [],
            "mcp_tools": [],
            "template": "entity_hygiene",
            "require_novel": True,
        }

    steps: list[PlanStep] = []
    for raw in skill.get("compose_steps") or []:
        steps.append(
            PlanStep(
                kind=str(raw.get("kind") or "nlp"),
                ref=str(raw.get("ref") or ""),
                package=str(raw.get("package") or ""),
                meta=dict(raw.get("meta") or {}),
            )
        )

    allowed_imports = list(skill.get("allowed_imports") or [])
    pip_deps = list(skill.get("pip_deps") or [])
    npm_deps = list(skill.get("npm_deps") or [])
    mcp_tools = list(skill.get("mcp_tools") or [])

    # Intersect with brief allowlists when provided
    if brief.allowed_libs:
        pip_deps = [d for d in pip_deps if d in brief.allowed_libs]
        for lib in brief.allowed_libs:
            info = lib_by_name(lib)
            if info:
                for root in info.get("import_roots") or []:
                    if root not in allowed_imports:
                        allowed_imports.append(root)
    if brief.allowed_npm:
        npm_deps = [d for d in npm_deps if d in brief.allowed_npm]
    if brief.allowed_mcp:
        mcp_tools = [t for t in mcp_tools if t in brief.allowed_mcp or t.split(".")[0] in brief.allowed_mcp]

    # Enrich evidence from discover + libs + npm
    evidence = [
        {"type": "skill", "id": skill.get("id"), "score": score_skill(skill, purpose)},
        {"type": "discover_top", "servers": [d.get("id") for d in discovered[:5]]},
        {"type": "ecosystem", "open_pip": brief.open_pip, "open_npm": brief.open_npm},
    ]
    for dep in pip_deps:
        info = lib_by_name(dep)
        if info:
            evidence.append({"type": "lib", "name": dep, "tags": info.get("purpose_tags")})
        else:
            evidence.append({"type": "lib_open", "name": dep})
    for dep in npm_deps:
        info = npm_by_name(dep)
        if info:
            evidence.append({"type": "npm", "name": dep, "tags": info.get("purpose_tags")})
        else:
            evidence.append({"type": "npm_open", "name": dep})

    if "linguini.invent.adapters.node_proxy" not in allowed_imports and npm_deps:
        allowed_imports.append("linguini.invent.adapters.node_proxy")

    plan = InventionPlan(
        name=name,
        need=purpose.need,
        skill_id=str(skill.get("id")),
        steps=steps,
        allowed_imports=allowed_imports,
        pip_deps=pip_deps,
        npm_deps=npm_deps,
        mcp_tools=mcp_tools,
        template=str(skill.get("template") or "entity_hygiene"),
        require_novel=bool(skill.get("require_novel", True)),
        expected_schema={"novel": True} if skill.get("require_novel", True) else {},
        evidence=evidence,
        discover=list(discovered[:10]),
    )
    return plan.freeze()


def rank_libs_for_purpose(purpose: ForgePurpose, *, limit: int = 10) -> list[dict[str, Any]]:
    toks = _tokens(purpose.need)
    scored: list[tuple[int, dict[str, Any]]] = []
    for pkg in list_libs():
        tags = set(pkg.get("purpose_tags") or [])
        score = sum(2 for t in tags if t in toks)
        scored.append((score, pkg))
    scored.sort(key=lambda x: (-x[0], x[1].get("name") or ""))
    out = []
    for score, pkg in scored[:limit]:
        row = dict(pkg)
        row["score"] = score
        out.append(row)
    return out


def rank_npm_for_purpose(purpose: ForgePurpose, *, limit: int = 10) -> list[dict[str, Any]]:
    toks = _tokens(purpose.need)
    scored: list[tuple[int, dict[str, Any]]] = []
    for pkg in list_npm():
        tags = set(pkg.get("purpose_tags") or [])
        score = sum(2 for t in tags if t in toks)
        scored.append((score, pkg))
    scored.sort(key=lambda x: (-x[0], x[1].get("name") or ""))
    out = []
    for score, pkg in scored[:limit]:
        row = dict(pkg)
        row["score"] = score
        out.append(row)
    return out
