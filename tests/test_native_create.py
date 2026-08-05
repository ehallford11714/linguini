"""E2E: Linguini must create, persist, reload, and run native novel tools."""

from pathlib import Path

from linguini import ForgePurpose, Linguini
from linguini.forge.purpose import IOExample
from linguini.mcp.server import TOOLS, dispatch, handle_tool


def test_create_native_tool_persists_and_runs(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    fr = ling.create_native_tool(
        "novel entity hygiene analyzer for claims",
        name="entity_hygiene_v1",
        template="entity_hygiene",
    )
    assert fr.ok and fr.persisted
    assert fr.native_name == "native.entity_hygiene_v1"
    reg = tmp_path / ".linguini" / "native_tools" / "registry.yaml"
    assert reg.exists()
    assert (tmp_path / ".linguini" / "native_tools" / "entity_hygiene_v1.py").exists()

    names = {t["name"] for t in ling.tools.list(layer="native")}
    assert "native.entity_hygiene_v1" in names

    out = ling.run_tool("native.entity_hygiene_v1", text="Acme Corp grew 12%. Hello World")
    assert out["novel"] is True
    assert "entities" in out
    assert "hygiene" in out
    assert "hello" in out["tokens"]
    assert "world" in out["tokens"]


def test_require_native_skips_leanback(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    result = ling.fulfill(
        ForgePurpose(
            need="tokenize and lowercase text",
            examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
            name="forced_native_tok",
            require_native=True,
            template="lowercase_tokens",
        )
    )
    assert result.mode in {"forge", "invent"}
    assert result.ok
    persisted = (
        (result.forge and result.forge.persisted)
        or (result.invent and result.invent.persisted)
    )
    assert persisted
    out = ling.run_tool("native.forced_native_tok", text="Hello World")
    assert out["novel"] is True
    assert out["tokens"] == ["hello", "world"]


def test_wrap_chain_as_native(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    fr = ling.wrap_chain(
        ["nlp.lowercase_tokens", "nlp.claim_hygiene"],
        name="tok_hygiene_chain",
        need="chain wrap tokenize then hygiene",
    )
    assert fr.ok and fr.persisted
    out = ling.run_tool("native.tok_hygiene_chain", text="Hello World")
    assert out["novel"] is True
    assert out["chain"] == ["nlp.lowercase_tokens", "nlp.claim_hygiene"]
    assert "outputs" in out


def test_cli_create_native(tmp_path: Path) -> None:
    from linguini.cli import main

    code = main(
        [
            "--root",
            str(tmp_path),
            "create",
            "--need",
            "novel analyze entities and hygiene",
            "--name",
            "cli_native_op",
            "--template",
            "entity_hygiene",
        ]
    )
    assert code == 0
    ling = Linguini(root=tmp_path)
    out = ling.run_tool("native.cli_native_op", text="Hello World")
    assert out["novel"] is True


def test_mcp_create_native_tool(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    assert any(t["name"] == "linguini_create_native" for t in TOOLS)
    result = handle_tool(
        ling,
        "linguini_create_native",
        {
            "need": "novel entity hygiene tool",
            "name": "mcp_native_op",
            "template": "entity_hygiene",
        },
    )
    assert result["isError"] is False
    out = ling.run_tool("native.mcp_native_op", text="Acme Corp")
    assert out["novel"] is True

    init = dispatch(ling, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init and init["result"]["serverInfo"]["name"] == "linguini"
    listed = dispatch(ling, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert listed and len(listed["result"]["tools"]) >= 6
