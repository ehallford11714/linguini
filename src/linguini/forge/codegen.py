"""Template codegen for novel ops (v0.1 heuristic compositions)."""

from __future__ import annotations

import re

from linguini.forge.purpose import ForgePurpose


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower()).strip("_")
    return s or "native_op"


def choose_template(purpose: ForgePurpose) -> str:
    need = purpose.need.lower()
    if "tokenize" in need and "hygiene" in need:
        return "compose_tokenize_hygiene"
    if "hygiene" in need or "spurious" in need:
        return "claim_hygiene"
    if "tokenize" in need:
        return "lowercase_tokens"
    return "compose_tokenize_hygiene"


def generate_tool_source(purpose: ForgePurpose, *, tool_name: str) -> str:
    """Generate a native tool module with run() composing NLP ops."""
    template = choose_template(purpose)
    slug = _slug(tool_name)
    if template == "lowercase_tokens":
        body = f'''
def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    tokens = nlp.lowercase_tokens(raw)
    return {{"tokens": tokens, "tool": "{slug}"}}
'''
    elif template == "claim_hygiene":
        body = f'''
def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    hygiene = nlp.claim_hygiene(raw)
    tokens = nlp.lowercase_tokens(raw)
    return {{"tokens": tokens, "hygiene": hygiene, "ok": hygiene["ok"], "tool": "{slug}"}}
'''
    else:
        body = f'''
def run(text: str = "", input: str = "", **kwargs):
    from linguini.suite.nlp import NLPSuite
    nlp = NLPSuite()
    raw = text or input
    return {{**nlp.compose_tokenize_hygiene(raw), "tool": "{slug}"}}
'''
    return f'"""Native tool {slug} forged by Linguini."""\nfrom __future__ import annotations\n{body}\n'


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
        if isinstance(exp, dict):
            for k, v in exp.items():
                src += f"    assert out[{k!r}] == {v!r}\n"
        else:
            src += f"    assert out == {exp!r}\n"
    if not purpose.examples:
        src += """

def test_smoke():
    mod = _load()
    out = mod.run(text="Hello World")
    assert isinstance(out, dict)
"""
    for inv in purpose.invariants:
        if "lowercase" in inv.lower():
            src += """

def test_invariant_lowercase():
    mod = _load()
    out = mod.run(text="Hello World")
    tokens = out.get("tokens") or []
    assert all(t == t.lower() for t in tokens)
"""
            break
    return src


def broken_source_for_repair_fixture(tool_name: str) -> str:
    slug = _slug(tool_name)
    return f'''"""Broken native {slug}."""
def run(text: str = "", input: str = "", **kwargs):
    return {{"tokens": ["WRONG"], "tool": "{slug}"}}
'''


def repair_source(purpose: ForgePurpose, *, tool_name: str, stderr: str = "") -> str:
    _ = stderr
    return generate_tool_source(purpose, tool_name=tool_name)
