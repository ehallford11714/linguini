from pathlib import Path

from linguini import ForgePurpose, IOExample, Linguini
from linguini.forge.codegen import broken_source_for_repair_fixture
from linguini.forge.forge import forge_tool
from linguini.forge.testloop import run_test_loop


def test_force_forge_persists_on_green(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    purpose = ForgePurpose(
        need="novel tokenize hygiene composite tool",
        examples=[
            IOExample(
                input="Hello World",
                expected={"tokens": ["hello", "world"]},
            )
        ],
        invariants=["output tokens are lowercase"],
        name="hygiene_tokens",
    )
    # force path via forge_tool directly so we always persist a native
    fr = forge_tool(purpose, root=tmp_path, tool_name="hygiene_tokens", persist=True)
    assert fr.ok and fr.persisted
    reg = tmp_path / ".linguini" / "native_tools" / "registry.yaml"
    assert reg.exists()
    ling.tools.reload_natives()
    names = {t["name"] for t in ling.tools.list(layer="native")}
    assert "native.hygiene_tokens" in names
    out = ling.run_tool("native.hygiene_tokens", text="Hello World")
    assert out["tokens"] == ["hello", "world"]


def test_no_persist_on_fail(tmp_path: Path) -> None:
    purpose = ForgePurpose(
        need="tokenize lowercase",
        examples=[IOExample(input="Hello", expected={"tokens": ["never_match"]})],
        name="bad_op",
    )
    fr = forge_tool(purpose, root=tmp_path, tool_name="bad_op", max_repairs=0, persist=True)
    assert fr.ok is False
    assert fr.persisted is False
    assert not (tmp_path / ".linguini" / "native_tools" / "registry.yaml").exists()


def test_repair_loop_recovers(tmp_path: Path) -> None:
    purpose = ForgePurpose(
        need="tokenize and lowercase text",
        examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
        name="repair_me",
    )
    broken = broken_source_for_repair_fixture("repair_me")
    loop = run_test_loop(purpose, tool_name="repair_me", max_repairs=2, initial_source=broken)
    assert loop.ok is True
    assert loop.attempts >= 2


def test_discover_fixture() -> None:
    from linguini.mcp.discover import discover_for_purpose

    rows = discover_for_purpose("grounding docs fetch entities")
    assert rows
    assert any(r["id"] == "fetch" for r in rows)
