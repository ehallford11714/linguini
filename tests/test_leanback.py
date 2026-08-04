from pathlib import Path

from linguini import ForgePurpose, IOExample, Linguini


def test_leanback_tokenize_no_forge(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    purpose = ForgePurpose(
        need="tokenize and lowercase text",
        examples=[IOExample(input="Hello World", expected={"tokens": ["hello", "world"]})],
        invariants=["output tokens are lowercase"],
    )
    r = ling.fulfill(purpose, forge_if_needed=True, persist=True)
    assert r.mode == "chain"
    assert r.ok is True
    assert not (tmp_path / ".linguini" / "native_tools" / "registry.yaml").exists()


def test_refuse_associative_only(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    purpose = ForgePurpose(
        need="because similar demand causes price rise",
        examples=[
            IOExample(
                input="Demand looks like last quarter so raise price",
                expected={"ok": False},
            )
        ],
    )
    r = ling.fulfill(purpose)
    assert r.mode == "refused"
