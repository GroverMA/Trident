"""Versioned runtime registry for professional research skills."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, Field


DEFAULT_SKILL_ROOT = Path(__file__).resolve().parents[2] / "knowledge_packs" / "research_skills"


class ResearchSkillManifest(BaseModel):
    skill_id: str
    version: str
    display_name: str
    description: str
    applies_to: list[str] = Field(min_length=1)
    module_ids: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    produced_artifacts: list[str] = Field(default_factory=list)
    hard_failures: list[str] = Field(default_factory=list)
    quality_rubric_version: str = "1.0"


class ResearchSkill(BaseModel):
    manifest: ResearchSkillManifest
    instructions: str
    content_hash: str


class ResearchSkillRegistry:
    def __init__(self, skills: list[ResearchSkill]) -> None:
        self._skills = {skill.manifest.skill_id: skill for skill in skills}

    @classmethod
    def load(cls, root: Path = DEFAULT_SKILL_ROOT) -> "ResearchSkillRegistry":
        skills: list[ResearchSkill] = []
        if not root.is_dir():
            return cls([])
        for manifest_path in sorted(root.glob("*/manifest.json")):
            skill_dir = manifest_path.parent
            skill_path = skill_dir / "SKILL.md"
            raw_manifest = manifest_path.read_bytes()
            raw_skill = skill_path.read_bytes()
            manifest = ResearchSkillManifest.model_validate_json(raw_manifest)
            digest = hashlib.sha256(raw_manifest + b"\0" + raw_skill).hexdigest()
            skills.append(ResearchSkill(
                manifest=manifest,
                instructions=raw_skill.decode("utf-8"),
                content_hash=digest,
            ))
        return cls(skills)

    def select(
        self, artifact: str, *, module_id: str | None = None
    ) -> list[ResearchSkill]:
        selected = []
        for skill in self._skills.values():
            manifest = skill.manifest
            if artifact not in manifest.applies_to and "all" not in manifest.applies_to:
                continue
            if module_id and manifest.module_ids and module_id not in manifest.module_ids:
                continue
            selected.append(skill)
        return sorted(selected, key=lambda item: item.manifest.skill_id)

    def prompt_context(self, artifact: str, *, module_id: str | None = None) -> str:
        selected = self.select(artifact, module_id=module_id)
        if not selected:
            return ""
        blocks = []
        for skill in selected:
            manifest = skill.manifest
            blocks.append(
                f"SKILL {manifest.skill_id}@{manifest.version}\n"
                f"Content hash: {skill.content_hash}\n"
                f"{skill.instructions}"
            )
        return "\n\n".join(blocks)

    def versions(self, artifact: str, *, module_id: str | None = None) -> dict[str, str]:
        return {
            skill.manifest.skill_id: skill.manifest.version
            for skill in self.select(artifact, module_id=module_id)
        }

    def hashes(self, artifact: str, *, module_id: str | None = None) -> dict[str, str]:
        return {
            skill.manifest.skill_id: skill.content_hash
            for skill in self.select(artifact, module_id=module_id)
        }
