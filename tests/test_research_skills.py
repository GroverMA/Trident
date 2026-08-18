from src.knowledge.skills import ResearchSkillRegistry
from src.knowledge.sop import load_active_sop


def test_registry_loads_all_professional_research_skills() -> None:
    registry = ResearchSkillRegistry.load()
    selected = registry.select("future")

    assert {skill.manifest.skill_id for skill in selected} == {
        "defining-industry-markets",
        "mapping-tracks-value-chain",
        "sizing-industry-markets",
        "analyzing-industry-competition",
        "analyzing-industry-drivers",
    }
    assert all(skill.manifest.version == "1.0.0" for skill in selected)
    assert all(len(skill.content_hash) == 64 for skill in selected)


def test_analysis_module_loads_only_its_matching_skill() -> None:
    sop = load_active_sop()
    context = sop.prompt_context("analysis", module_id="competitive_landscape")

    assert "SKILL analyzing-industry-competition@1.0.0" in context
    assert "SKILL analyzing-industry-drivers@1.0.0" not in context
    assert sop.skill_versions("analysis", module_id="competitive_landscape") == {
        "analyzing-industry-competition": "1.0.0"
    }


def test_future_inherits_all_approved_research_methods() -> None:
    sop = load_active_sop()

    assert len(sop.skill_versions("future")) == 5
    assert set(sop.skill_versions("future")) == set(sop.skill_hashes("future"))
