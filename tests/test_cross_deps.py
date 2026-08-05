"""Pip/npm catalogs, name sanitization, open-mode gates, cross-runtime skill."""

from pathlib import Path

import pytest

from linguini import Linguini
from linguini.invent.catalogs import is_npm_allowlisted, is_pip_allowlisted, list_npm
from linguini.invent.deps import ensure_npm_deps, ensure_pip_deps, node_available
from linguini.invent.pkg_names import npm_base_name, validate_npm_spec, validate_pip_spec
from linguini.sandbox.policy import SandboxPolicy


def test_pip_npm_name_validation() -> None:
    assert validate_pip_spec("beautifulsoup4") == "beautifulsoup4"
    assert validate_pip_spec("httpx==0.27.0").startswith("httpx")
    with pytest.raises(ValueError):
        validate_pip_spec("evil; rm -rf /")
    assert npm_base_name("marked@9.0.0") == "marked"
    assert validate_npm_spec("@scope/pkg") == "@scope/pkg"
    with pytest.raises(ValueError):
        validate_npm_spec("marked && reboot")


def test_catalogs_expanded() -> None:
    assert is_pip_allowlisted("networkx")
    assert is_pip_allowlisted("pandas")
    assert is_npm_allowlisted("marked")
    assert is_npm_allowlisted("cheerio")
    assert len(list_npm()) >= 10


def test_open_pip_blocked_without_flag(tmp_path: Path) -> None:
    r = ensure_pip_deps(tmp_path, ["some-unknown-pkg-xyz"], allow_open_pip=False)
    assert r.ok is False
    assert any("not allowlisted" in e for e in r.errors)


def test_open_npm_blocked_without_flag(tmp_path: Path) -> None:
    r = ensure_npm_deps(tmp_path, ["left-pad"], allow_open_npm=False)
    assert r.ok is False
    assert any("not allowlisted" in e for e in r.errors)


@pytest.mark.skipif(not node_available(), reason="node/npm not on PATH")
def test_invent_md_npm_hygiene(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path, policy=SandboxPolicy(allow_npm_install=True))
    ir = ling.invent(
        "markdown npm parse with entity hygiene cross runtime",
        name="md_cross",
        prefer_skill="md_npm_hygiene",
    )
    assert ir.ok and ir.persisted, ir.reason
    assert ir.deps and "marked" in (ir.deps.get("npm_installed") or ["marked"])
    out = ling.run_tool(
        "native.md_cross",
        text="# Acme Corp\n\nGrew **12%**.",
    )
    assert out["novel"] is True
    assert out.get("ecosystems") == ["npm", "pip", "nlp"]
    assert "entities" in out
