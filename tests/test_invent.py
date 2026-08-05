"""Tool inventor: compose → lint → pytest → persist."""

from pathlib import Path

from linguini import Linguini
from linguini.invent.adapters.mcp_proxy import call_mcp_tool, list_mcp_tool_schemas
from linguini.invent.catalogs import is_pip_allowlisted, list_skills
from linguini.invent.codegen import generate_from_plan
from linguini.invent.composer import compose_plan
from linguini.invent.lint import lint_source
from linguini.invent.plan import InventionPlan, PlanStep
from linguini.forge.purpose import ForgePurpose, IOExample


def test_skills_and_libs_catalog() -> None:
    skills = list_skills()
    assert any(s["id"] == "entity_hygiene" for s in skills)
    assert is_pip_allowlisted("beautifulsoup4")
    assert not is_pip_allowlisted("totally-unknown-pkg-xyz")


def test_mcp_tool_schemas() -> None:
    tools = list_mcp_tool_schemas()
    assert any(t["full_name"] == "fetch.fetch" for t in tools)
    out = call_mcp_tool("fetch.fetch", arguments={"text": "hello"})
    assert out["ok"] is True
    assert out["stub"] is True


def test_compose_plan_freezes_bounds() -> None:
    purpose = ForgePurpose(need="novel entity hygiene analyzer")
    plan = compose_plan(purpose, name="x")
    assert plan.frozen
    assert plan.bounds_hash
    assert plan.skill_id == "entity_hygiene"


def test_lint_rejects_disallowed_import() -> None:
    plan = InventionPlan(
        name="bad",
        need="x",
        skill_id="entity_hygiene",
        allowed_imports=["linguini"],
        template="entity_hygiene",
    ).freeze()
    bad = "import socket\ndef run(text=''): return {'novel': True}\n"
    result = lint_source(bad, plan)
    assert result.ok is False
    assert any("socket" in v or "disallowed" in v for v in result.violations)


def test_lint_accepts_plan_source() -> None:
    purpose = ForgePurpose(need="novel entity analyze")
    plan = compose_plan(purpose, name="ok_tool")
    source = generate_from_plan(plan)
    result = lint_source(source, plan)
    assert result.ok, result.violations


def test_invent_entity_hygiene(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    ir = ling.invent(
        "novel entity hygiene analyzer for claims",
        name="invented_claim",
        prefer_skill="entity_hygiene",
    )
    assert ir.ok and ir.persisted
    assert ir.lint_ok and ir.tests_ok
    assert ir.plan and ir.plan.bounds_hash
    out = ling.run_tool("native.invented_claim", text="Acme Corp grew 12%.")
    assert out["novel"] is True
    assert "entities" in out


def test_invent_mcp_chain_wrap(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    ir = ling.invent(
        "chain mcp fetch and memory with hygiene",
        name="mcp_chain_tool",
        prefer_skill="mcp_chain_wrap",
    )
    assert ir.ok and ir.persisted, ir.reason
    out = ling.run_tool("native.mcp_chain_tool", text="Ground Acme claim")
    assert out["novel"] is True
    assert "fetch.fetch" in out["chain"]


def test_invent_cli(tmp_path: Path) -> None:
    from linguini.cli import main

    code = main(
        [
            "--root",
            str(tmp_path),
            "invent",
            "--need",
            "novel entity hygiene",
            "--name",
            "cli_invented",
            "--skill",
            "entity_hygiene",
        ]
    )
    assert code == 0
    ling = Linguini(root=tmp_path)
    assert "native.cli_invented" in {t["name"] for t in ling.tools.list(layer="native")}


def test_create_native_routes_through_invent(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    fr = ling.create_native_tool(
        "novel analyze entities",
        name="via_create",
        template="entity_hygiene",
    )
    assert fr.ok and fr.persisted
    assert fr.mode == "invent"
