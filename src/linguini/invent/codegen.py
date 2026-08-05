"""Deterministic template stitch from InventionPlan (compose-first, no LLM)."""

from __future__ import annotations

import re
from typing import Any

from linguini.forge.purpose import ForgePurpose, IOExample
from linguini.invent.plan import InventionPlan


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower()).strip("_")
    return s or "native_op"


def generate_from_plan(plan: InventionPlan, *, tool_name: str | None = None) -> str:
    """Stitch novel native source from a frozen plan."""
    plan.assert_frozen()
    slug = _slug(tool_name or plan.name)
    template = plan.template

    if template == "html_ground_parse":
        return _html_ground_parse(slug, plan)
    if template == "mcp_chain_wrap":
        return _mcp_chain_wrap(slug, plan)
    if template == "md_npm_hygiene":
        return _md_npm_hygiene(slug, plan)
    if template == "tokenize_hygiene":
        return _tokenize_hygiene(slug)
    if template == "lowercase_tokens":
        return _lowercase_tokens(slug)
    # default entity_hygiene
    return _entity_hygiene(slug, plan)


def _entity_hygiene(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native tool {slug} invented by Linguini (skill={plan.skill_id})."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    result = nlp.compose_entity_hygiene(raw)
    result["tool"] = "{slug}"
    result["novel"] = True
    result["skill_id"] = {plan.skill_id!r}
    result["bounds_hash"] = {plan.bounds_hash!r}
    result["purpose"] = {plan.need!r}
    return result
'''


def _tokenize_hygiene(slug: str) -> str:
    return f'''"""Native tool {slug} invented by Linguini."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    base = nlp.compose_tokenize_hygiene(raw)
    base["lemmas"] = nlp.lemmas(raw)
    base["tool"] = "{slug}"
    base["novel"] = True
    return base
'''


def _lowercase_tokens(slug: str) -> str:
    return f'''"""Native tool {slug} invented by Linguini."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    tokens = nlp.lowercase_tokens(raw)
    lemmas = nlp.lemmas(raw)
    return {{"tokens": tokens, "lemmas": lemmas, "tool": "{slug}", "novel": True}}
'''


def _html_ground_parse(slug: str, plan: InventionPlan) -> str:
    mcp = plan.mcp_tools[0] if plan.mcp_tools else "fetch.fetch"
    return f'''"""Native tool {slug} — HTML parse + entity hygiene (lib + nlp + mcp stub)."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from bs4 import BeautifulSoup
    from linguini.suite.nlp import NLPSuite
    from linguini.invent.adapters.mcp_proxy import call_mcp_tool

    raw = text or input
    # Optional MCP grounding stub (fixture)
    mcp_out = call_mcp_tool({mcp!r}, arguments={{"text": raw}})
    soup = BeautifulSoup(raw, "html.parser")
    plain = soup.get_text(" ", strip=True) or raw
    nlp = NLPSuite()
    result = nlp.compose_entity_hygiene(plain)
    result["tool"] = "{slug}"
    result["novel"] = True
    result["html_text"] = plain
    result["mcp"] = mcp_out
    result["skill_id"] = {plan.skill_id!r}
    result["bounds_hash"] = {plan.bounds_hash!r}
    return result
'''


def _md_npm_hygiene(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native tool {slug} — npm marked + Python entity hygiene (cross-runtime)."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    from linguini.invent.adapters.node_proxy import markdown_to_text

    raw = text or input
    md = markdown_to_text(raw)
    plain = (md.get("text") if md.get("ok") else None) or raw
    result = NLPSuite().compose_entity_hygiene(plain)
    result["tool"] = "{slug}"
    result["novel"] = True
    result["npm"] = md
    result["skill_id"] = {plan.skill_id!r}
    result["bounds_hash"] = {plan.bounds_hash!r}
    result["ecosystems"] = ["npm", "pip", "nlp"]
    return result
'''


def _mcp_chain_wrap(slug: str, plan: InventionPlan) -> str:
    tools = plan.mcp_tools or ["fetch.fetch", "memory.search"]
    tools_lit = repr(tools)
    return f'''"""Native tool {slug} — MCP stub chain + hygiene."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    from linguini.invent.adapters.mcp_proxy import call_mcp_tool

    raw = text or input
    steps = {tools_lit}
    outputs = []
    current = raw
    for tool_id in steps:
        out = call_mcp_tool(tool_id, arguments={{"text": current if isinstance(current, str) else raw, "query": raw}})
        outputs.append({{"tool": tool_id, "output": out}})
        inner = (out.get("output") or {{}}).get("text")
        if isinstance(inner, str) and inner:
            current = inner
    hygiene = NLPSuite().claim_hygiene(raw)
    return {{
        "tool": "{slug}",
        "novel": True,
        "chain": steps,
        "outputs": outputs,
        "hygiene": hygiene,
        "final": current,
        "skill_id": {plan.skill_id!r},
        "bounds_hash": {plan.bounds_hash!r},
    }}
'''


def generate_tests_from_plan(
    plan: InventionPlan,
    purpose: ForgePurpose,
    *,
    module_filename: str = "TOOL_MODULE.py",
) -> str:
    examples = list(purpose.examples)
    if not examples:
        # pull from skill defaults via expected_schema
        examples = [IOExample(input="Acme Corp grew 12%.", expected={"novel": True})]

    src = f'''from __future__ import annotations
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name({module_filename!r})

def _load():
    spec = importlib.util.spec_from_file_location("native_under_test", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod
'''
    for i, ex in enumerate(examples):
        inp = ex.input if isinstance(ex.input, str) else str(ex.input)
        exp = ex.expected
        src += f"\n\ndef test_example_{i}():\n"
        src += "    mod = _load()\n"
        src += f"    out = mod.run(text={inp!r})\n"
        src += "    assert isinstance(out, dict)\n"
        if plan.require_novel:
            src += "    assert out.get('novel') is True\n"
        if isinstance(exp, dict):
            for k, v in exp.items():
                if k == "novel":
                    continue
                src += f"    assert out[{k!r}] == {v!r}\n"
    src += """

def test_bounds_marker():
    mod = _load()
    out = mod.run(text="Hello World")
    assert out.get("novel") is True
"""
    for inv in purpose.invariants:
        if "lowercase" in inv.lower():
            src += """

def test_invariant_lowercase():
    mod = _load()
    out = mod.run(text="Hello World")
    tokens = out.get("tokens") or []
    assert all(isinstance(t, str) and t == t.lower() for t in tokens)
"""
            break
    return src


def purpose_from_plan_examples(plan: InventionPlan, skill: dict[str, Any] | None = None) -> list[IOExample]:
    out: list[IOExample] = []
    if skill:
        for ex in skill.get("example_tests") or []:
            out.append(IOExample(input=ex.get("input", ""), expected=ex.get("expected")))
    if not out:
        out.append(IOExample(input="Acme Corp grew 12%.", expected={"novel": True}))
    return out
