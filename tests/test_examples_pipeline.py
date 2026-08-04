"""Smoke-test the documented create → use pipeline (mirrors examples/)."""

from pathlib import Path

from linguini import ForgePurpose, IOExample, Linguini


def test_example_create_then_use(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    fr = ling.create_native_tool(
        "novel claim analyzer: entities + hygiene",
        name="claim_analyzer",
        template="entity_hygiene",
        examples=[IOExample(input="Acme Corp grew 12%.", expected={"novel": True})],
    )
    assert fr.persisted

    # Fresh client = reload registry (same as example 02)
    ling2 = Linguini(root=tmp_path)
    names = {t["name"] for t in ling2.tools.list(layer="native")}
    assert "native.claim_analyzer" in names
    out = ling2.run_tool("native.claim_analyzer", text="Acme Corp grew 12%.")
    assert out["novel"] is True
    assert "entities" in out


def test_example_wrap_and_leanback(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    fr = ling.wrap_chain(
        ["nlp.lowercase_tokens", "nlp.claim_hygiene"],
        name="tok_then_hygiene",
    )
    assert fr.persisted
    out = ling.run_tool("native.tok_then_hygiene", text="Hello")
    assert out["novel"] is True
    assert out["chain"][0] == "nlp.lowercase_tokens"

    lean = ling.fulfill(
        ForgePurpose(
            need="tokenize and lowercase text",
            examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
        )
    )
    assert lean.mode == "chain"
