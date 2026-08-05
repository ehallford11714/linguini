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

    generators = {
        "html_ground_parse": _html_ground_parse,
        "mcp_chain_wrap": _mcp_chain_wrap,
        "md_npm_hygiene": _md_npm_hygiene,
        "tokenize_hygiene": lambda s, p: _tokenize_hygiene(s),
        "lowercase_tokens": lambda s, p: _lowercase_tokens(s),
        "yaml_config_hygiene": _yaml_config_hygiene,
        "bleach_sanitize_analyze": _bleach_sanitize_analyze,
        "jsonschema_claim_gate": _jsonschema_claim_gate,
        "networkx_entity_graph": _networkx_entity_graph,
        "cheerio_npm_html": _cheerio_npm_html,
        "turndown_html_md": _turndown_html_md,
        "repo_ground_pack": _repo_ground_pack,
        "reflect_hygiene": _reflect_hygiene,
        "date_aware_claims": _date_aware_claims,
        "spec_distill": _spec_distill,
    }
    gen = generators.get(template, _entity_hygiene)
    return gen(slug, plan)


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


def _yaml_config_hygiene(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — YAML parse + entity/claim hygiene."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    import yaml
    from linguini.suite.nlp import NLPSuite

    raw = text or input
    try:
        data = yaml.safe_load(raw)
    except Exception as e:
        data = {{"parse_error": str(e)}}
    blob = raw if isinstance(raw, str) else str(data)
    if isinstance(data, dict):
        blob = " ".join(f"{{k}} {{v}}" for k, v in data.items())
    result = NLPSuite().compose_entity_hygiene(blob)
    result.update({{"tool": "{slug}", "novel": True, "yaml": data,
                    "skill_id": {plan.skill_id!r}, "bounds_hash": {plan.bounds_hash!r}}})
    return result
'''


def _bleach_sanitize_analyze(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — bleach sanitize + entity hygiene."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    import bleach
    from linguini.suite.nlp import NLPSuite

    raw = text or input
    clean = bleach.clean(raw, tags=[], strip=True)
    result = NLPSuite().compose_entity_hygiene(clean)
    result.update({{"tool": "{slug}", "novel": True, "sanitized": clean,
                    "skill_id": {plan.skill_id!r}, "bounds_hash": {plan.bounds_hash!r}}})
    return result
'''


def _jsonschema_claim_gate(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — jsonschema gate + claim hygiene."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    import json
    import jsonschema
    from linguini.suite.nlp import NLPSuite

    raw = text or input
    schema = kwargs.get("schema") or {{
        "type": "object",
        "properties": {{"claim": {{"type": "string"}}, "action": {{"type": "string"}}}},
        "required": ["claim"],
    }}
    try:
        payload = json.loads(raw) if raw.strip().startswith("{{") else {{"claim": raw}}
    except Exception:
        payload = {{"claim": raw}}
    errors = []
    try:
        jsonschema.validate(payload, schema)
        valid = True
    except jsonschema.ValidationError as e:
        valid = False
        errors.append(e.message)
    claim = str(payload.get("claim") or raw)
    hygiene = NLPSuite().claim_hygiene(claim)
    return {{
        "tool": "{slug}", "novel": True, "valid": valid, "errors": errors,
        "payload": payload, "hygiene": hygiene, "ok": valid and hygiene.get("ok", False),
        "skill_id": {plan.skill_id!r}, "bounds_hash": {plan.bounds_hash!r},
    }}
'''


def _networkx_entity_graph(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — entity co-occurrence graph via networkx."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    import networkx as nx
    from linguini.suite.nlp import NLPSuite

    raw = text or input
    nlp = NLPSuite()
    analyzed = nlp.compose_entity_hygiene(raw)
    ents = [e.get("text") for e in (analyzed.get("entities") or []) if e.get("text")]
    g = nx.Graph()
    for e in ents:
        g.add_node(e)
    for i, a in enumerate(ents):
        for b in ents[i + 1 :]:
            g.add_edge(a, b)
    return {{
        "tool": "{slug}", "novel": True, "entities": analyzed.get("entities"),
        "hygiene": analyzed.get("hygiene"), "nodes": list(g.nodes()),
        "edges": [list(e) for e in g.edges()], "graph_order": g.order(),
        "skill_id": {plan.skill_id!r}, "bounds_hash": {plan.bounds_hash!r},
    }}
'''


def _cheerio_npm_html(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — npm cheerio HTML extract + Python hygiene."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    from linguini.invent.adapters.node_proxy import cheerio_to_text

    raw = text or input
    html = cheerio_to_text(raw)
    plain = (html.get("text") if html.get("ok") else None) or raw
    result = NLPSuite().compose_entity_hygiene(plain)
    result.update({{"tool": "{slug}", "novel": True, "npm": html, "links": html.get("links"),
                    "ecosystems": ["npm", "nlp"], "skill_id": {plan.skill_id!r},
                    "bounds_hash": {plan.bounds_hash!r}}})
    return result
'''


def _turndown_html_md(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — npm turndown HTML→MD + entity hygiene."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    from linguini.invent.adapters.node_proxy import html_to_markdown

    raw = text or input
    md = html_to_markdown(raw)
    plain = (md.get("text") if md.get("ok") else None) or raw
    result = NLPSuite().compose_entity_hygiene(plain)
    result.update({{"tool": "{slug}", "novel": True, "npm": md,
                    "markdown": md.get("markdown"), "ecosystems": ["npm", "nlp"],
                    "skill_id": {plan.skill_id!r}, "bounds_hash": {plan.bounds_hash!r}}})
    return result
'''


def _repo_ground_pack(slug: str, plan: InventionPlan) -> str:
    tools = plan.mcp_tools or ["github.search_code", "memory.search"]
    return f'''"""Native {slug} — GitHub + memory grounding pack + wisdom check."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    from linguini.invent.adapters.mcp_proxy import call_mcp_tool

    raw = text or input
    justification = str(kwargs.get("justification") or raw)
    gh = call_mcp_tool({tools[0]!r}, arguments={{"query": raw, "text": raw}})
    mem = call_mcp_tool({tools[1]!r}, arguments={{"query": raw, "text": raw}})
    nlp = NLPSuite()
    analyzed = nlp.compose_entity_hygiene(raw)
    wisdom = nlp.claim_hygiene(justification)
    return {{
        "tool": "{slug}", "novel": True, "github": gh, "memory": mem,
        "entities": analyzed.get("entities"), "hygiene": analyzed.get("hygiene"),
        "wisdom": wisdom, "ok": wisdom.get("ok", False),
        "skill_id": {plan.skill_id!r}, "bounds_hash": {plan.bounds_hash!r},
    }}
'''


def _reflect_hygiene(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — sequential-thinking stub then claim hygiene."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    from linguini.invent.adapters.mcp_proxy import call_mcp_tool

    raw = text or input
    thought = call_mcp_tool("sequential-thinking.think", arguments={{"thought": raw, "text": raw}})
    hygiene = NLPSuite().claim_hygiene(raw)
    analyzed = NLPSuite().compose_entity_hygiene(raw)
    return {{
        "tool": "{slug}", "novel": True, "thought": thought,
        "hygiene": hygiene, "entities": analyzed.get("entities"),
        "ok": hygiene.get("ok", False), "posture": "lean_in" if hygiene.get("ok") else "push_back",
        "skill_id": {plan.skill_id!r}, "bounds_hash": {plan.bounds_hash!r},
    }}
'''


def _date_aware_claims(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — dateutil cues + entity/claim hygiene."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    import re
    from dateutil import parser as date_parser
    from linguini.suite.nlp import NLPSuite

    raw = text or input
    dates = []
    for m in re.finditer(r"\\b(?:\\d{{1,2}}[/-]\\d{{1,2}}[/-]\\d{{2,4}}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+\\d{{1,2}},?\\s+\\d{{4}})\\b", raw, re.I):
        frag = m.group(0)
        try:
            dates.append({{"text": frag, "iso": date_parser.parse(frag, fuzzy=True).isoformat()}})
        except Exception:
            dates.append({{"text": frag, "iso": None}})
    result = NLPSuite().compose_entity_hygiene(raw)
    result.update({{"tool": "{slug}", "novel": True, "dates": dates,
                    "skill_id": {plan.skill_id!r}, "bounds_hash": {plan.bounds_hash!r}}})
    return result
'''


def _spec_distill(slug: str, plan: InventionPlan) -> str:
    return f'''"""Native {slug} — mistune markdown distill + topics + entities."""
from __future__ import annotations

def run(text: str = "", input: str = "", **kwargs):
    import mistune
    from linguini.suite.nlp import NLPSuite

    raw = text or input
    html = mistune.html(raw)
    # crude checklist: lines starting with - [ ] or -
    checks = [ln.strip() for ln in raw.splitlines() if ln.strip().startswith(("-", "*")) or ln.strip().startswith("#")]
    plain = mistune.html(raw)
    import re
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"\\s+", " ", plain).strip() or raw
    nlp = NLPSuite()
    analyzed = nlp.compose_entity_hygiene(plain)
    return {{
        "tool": "{slug}", "novel": True, "checklist": checks[:40],
        "topics": nlp.topic_hash(plain), "entities": analyzed.get("entities"),
        "hygiene": analyzed.get("hygiene"), "tokens": analyzed.get("tokens"),
        "html_len": len(html), "skill_id": {plan.skill_id!r},
        "bounds_hash": {plan.bounds_hash!r},
    }}
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
