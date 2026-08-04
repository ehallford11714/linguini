"""Codegen for novel native ops (compositions, not bare aliases)."""

from __future__ import annotations

import re
from typing import Sequence

from linguini.forge.purpose import ForgePurpose


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower()).strip("_")
    return s or "native_op"


def choose_template(purpose: ForgePurpose) -> str:
    if purpose.template and purpose.template != "auto":
        return purpose.template
    need = purpose.need.lower()
    if "entity" in need or "analyze" in need or "novel" in need or purpose.require_native:
        return "entity_hygiene"
    if "chain" in need or (purpose.must_compose and len(purpose.must_compose) >= 2):
        return "chain_wrap"
    if "tokenize" in need and "hygiene" in need:
        return "tokenize_hygiene"
    if "hygiene" in need or "spurious" in need:
        return "tokenize_hygiene"
    if "tokenize" in need:
        return "lowercase_tokens"
    return "entity_hygiene"


def generate_tool_source(
    purpose: ForgePurpose,
    *,
    tool_name: str,
    chain_steps: Sequence[str] | None = None,
) -> str:
    """Generate a native tool module with run() — novel ops compose multiple suite calls."""
    template = choose_template(purpose)
    slug = _slug(tool_name)
    steps = list(chain_steps or purpose.must_compose or [])

    if template == "chain_wrap" and steps:
        steps_lit = repr(steps)
        body = f'''
def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    steps = {steps_lit}
    outputs = []
    current = raw
    for step in steps:
        out = nlp.run(step, text=current if isinstance(current, str) else raw, input=raw)
        outputs.append({{"tool": step, "output": out}})
        current = out
    return {{
        "tool": "{slug}",
        "novel": True,
        "chain": steps,
        "outputs": outputs,
        "final": current,
    }}
'''
    elif template == "lowercase_tokens":
        body = f'''
def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    tokens = nlp.lowercase_tokens(raw)
    lemmas = nlp.lemmas(raw)
    return {{"tokens": tokens, "lemmas": lemmas, "tool": "{slug}", "novel": True}}
'''
    elif template == "tokenize_hygiene":
        body = f'''
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
    else:  # entity_hygiene — default novel composite
        body = f'''
def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    result = nlp.compose_entity_hygiene(raw)
    result["tool"] = "{slug}"
    result["novel"] = True
    result["purpose"] = {purpose.need!r}
    return result
'''

    return (
        f'"""Native tool {slug} forged by Linguini (novel op)."""\n'
        f"from __future__ import annotations\n{body}\n"
    )


def generate_pytest_source(purpose: ForgePurpose, *, module_filename: str = "TOOL_MODULE.py") -> str:
    """Generate real pytest module from purpose examples."""
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
    for i, ex in enumerate(purpose.examples):
        inp = ex.input if isinstance(ex.input, str) else str(ex.input)
        exp = ex.expected
        src += f"\n\ndef test_example_{i}():\n"
        src += "    mod = _load()\n"
        src += f"    out = mod.run(text={inp!r})\n"
        src += "    assert isinstance(out, dict)\n"
        src += "    assert out.get('novel') is True\n"
        if isinstance(exp, dict):
            for k, v in exp.items():
                src += f"    assert out[{k!r}] == {v!r}\n"
        elif exp is not None:
            src += f"    assert out == {exp!r}\n"
    if not purpose.examples:
        src += """

def test_smoke_novel():
    mod = _load()
    out = mod.run(text="Acme Corp looks strong. Hello World")
    assert isinstance(out, dict)
    assert out.get("novel") is True
    assert "tokens" in out or "final" in out or "chain" in out
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
    if purpose.require_native or choose_template(purpose) != "lowercase_tokens":
        src += """

def test_novelty_not_alias():
    mod = _load()
    out = mod.run(text="Hello World")
    # Novel natives expose composite fields beyond a bare token list
    assert out.get("novel") is True
    assert (
        ("entities" in out)
        or ("chain" in out)
        or ("hygiene" in out)
        or ("lemmas" in out)
    )
"""
    return src


def broken_source_for_repair_fixture(tool_name: str) -> str:
    slug = _slug(tool_name)
    return f'''"""Broken native {slug}."""
def run(text: str = "", input: str = "", **kwargs):
    return {{"tokens": ["WRONG"], "tool": "{slug}", "novel": True}}
'''


def repair_source(
    purpose: ForgePurpose,
    *,
    tool_name: str,
    stderr: str = "",
    chain_steps: Sequence[str] | None = None,
) -> str:
    _ = stderr
    return generate_tool_source(purpose, tool_name=tool_name, chain_steps=chain_steps)
