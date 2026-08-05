"""New inventable skills are registered and a sample invents cleanly."""

from pathlib import Path

from linguini import Linguini
from linguini.invent.catalogs import list_skills, skill_by_id
from linguini.invent.codegen import generate_from_plan
from linguini.invent.composer import compose_plan
from linguini.invent.lint import lint_source
from linguini.forge.purpose import ForgePurpose


EXPECTED_NEW = {
    "yaml_config_hygiene",
    "bleach_sanitize_analyze",
    "jsonschema_claim_gate",
    "networkx_entity_graph",
    "cheerio_npm_html",
    "turndown_html_md",
    "repo_ground_pack",
    "reflect_hygiene",
    "date_aware_claims",
    "spec_distill",
}


def test_all_new_skills_registered() -> None:
    ids = {s["id"] for s in list_skills()}
    assert EXPECTED_NEW <= ids
    assert len(ids) >= 16


def test_each_new_skill_lints() -> None:
    for sid in sorted(EXPECTED_NEW):
        skill = skill_by_id(sid)
        assert skill is not None
        purpose = ForgePurpose(need=skill["description"], template=sid)
        plan = compose_plan(purpose, name=f"t_{sid}", brief=__import__("linguini.invent.plan", fromlist=["InventionBrief"]).InventionBrief(prefer_skill=sid))
        source = generate_from_plan(plan)
        result = lint_source(source, plan)
        assert result.ok, (sid, result.violations)


def test_invent_reflect_and_yaml(tmp_path: Path) -> None:
    ling = Linguini(root=tmp_path)
    r1 = ling.invent("reflect then hygiene gate", name="reflect_gate", prefer_skill="reflect_hygiene")
    assert r1.ok and r1.persisted, r1.reason
    out = ling.run_tool("native.reflect_gate", text="Demand looks like last quarter so raise price")
    assert out["novel"] is True
    assert out["posture"] == "push_back"

    r2 = ling.invent("yaml config hygiene", name="yaml_gate", prefer_skill="yaml_config_hygiene")
    assert r2.ok and r2.persisted, r2.reason
    y = ling.run_tool("native.yaml_gate", text="claim: Acme Corp grew 12%\naction: hold")
    assert y["novel"] is True
    assert "yaml" in y
