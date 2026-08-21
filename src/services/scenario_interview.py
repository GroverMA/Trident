"""Scenario-pack-driven adaptive interview orchestration.

The service contains no PE/VC/growth branches.  All scenario differences are
declared by the registered pack, while session state is stored on ProjectState.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.core.registry import ExtensionRegistry
from src.models.interview import (
    EntityProfileArtifact,
    InterviewStatus,
    InterviewTurn,
    ScenarioInterviewArtifact,
)
from src.state.project import ProjectState


class ScenarioInterviewError(ValueError):
    pass


class ScenarioInterviewService:
    def __init__(self, packs: ExtensionRegistry) -> None:
        self._packs = packs

    def _policy(self, project: ProjectState) -> dict:
        pack = self._packs.get(project.scenario_pack, project.scenario_pack_version)
        return dict(pack.interview_policy())

    def start(self, project: ProjectState, *, restart: bool = False) -> ProjectState:
        if project.interview_session_artifact is not None and not restart:
            return project
        policy = self._policy(project)
        questions = [str(item).strip() for item in policy.get("starter_questions", []) if str(item).strip()]
        if not questions:
            raise ScenarioInterviewError("该场景不需要诊断访谈")
        topics = [str(item) for item in policy.get("diagnostic_topics", [])]
        if len(topics) != len(questions):
            topics = [f"topic_{index + 1}" for index in range(len(questions))]
        artifact = ScenarioInterviewArtifact(
            scenario_id=project.scenario_pack,
            scenario_version=project.scenario_pack_version,
            objective=project.company_strategy_objective or project.research_objective,
            turns=[InterviewTurn(topic_id=topics[0], question=questions[0])],
            remaining_topics=topics,
            suggested_uploads=[str(item) for item in policy.get("suggested_uploads", [])],
        )
        return project.model_copy(update={"interview_session_artifact": artifact, "entity_profile_artifact": None})

    def answer(self, project: ProjectState, answer: str) -> ProjectState:
        text = answer.strip()
        if not text:
            raise ScenarioInterviewError("访谈回答不能为空")
        session = project.interview_session_artifact
        if session is None:
            raise ScenarioInterviewError("请先开始诊断访谈")
        current = session.current_turn
        if current is None:
            raise ScenarioInterviewError("当前访谈已经完成")
        quality = "sufficient" if len(text) >= 12 else "needs_validation"
        turns = [
            turn.model_copy(update={"answer": text, "answer_quality": quality})
            if turn.turn_id == current.turn_id else turn
            for turn in session.turns
        ]
        covered = [*session.covered_topics, current.topic_id]
        remaining = [topic for topic in session.remaining_topics if topic != current.topic_id]
        policy = self._policy(project)
        questions = [str(item) for item in policy.get("starter_questions", [])]
        topics = [str(item) for item in policy.get("diagnostic_topics", [])]
        if len(topics) != len(questions):
            topics = [f"topic_{index + 1}" for index in range(len(questions))]
        if remaining:
            next_topic = remaining[0]
            next_index = topics.index(next_topic)
            turns.append(InterviewTurn(topic_id=next_topic, question=questions[next_index]))
            status = InterviewStatus.IN_PROGRESS
            profile = None
        else:
            status = InterviewStatus.COMPLETED
            profile = self._profile(project, turns)
        updated = session.model_copy(update={
            "turns": turns,
            "covered_topics": covered,
            "remaining_topics": remaining,
            "status": status,
            "updated_at": datetime.now(UTC),
        })
        return project.model_copy(update={"interview_session_artifact": updated, "entity_profile_artifact": profile})

    @staticmethod
    def _profile(project: ProjectState, turns: list[InterviewTurn]) -> EntityProfileArtifact:
        answers = [turn.answer or "" for turn in turns]
        joined = " ".join(answers)
        data_led = any(word in joined for word in ("数据", "指标", "财务", "报表", "毛利", "订单"))
        decisive = any(word in joined for word in ("拍板", "快速", "试错", "果断"))
        gaps = [turn.topic_id for turn in turns if turn.answer_quality == "needs_validation"]
        return EntityProfileArtifact(
            scenario_id=project.scenario_pack,
            entity_name=project.target_company or project.project_name,
            objective=project.company_strategy_objective or project.research_objective,
            operating_portrait=(
                "已有部分关键经营数据，下一步需要统一口径并补齐细分维度。"
                if data_led else "当前判断较依赖管理层口述，需先建立最小数据底座并逐项验证。"
            ),
            decision_style=(
                "管理层偏快速判断与迭代，应设置复盘点和止损条件。"
                if decisive else "管理层偏审慎共识，应显性记录假设、证据、责任人与确认节点。"
            ),
            research_next_step="依据场景包进入专业研究内核，并把画像中的事实、假设和缺口分别处理。",
            known_facts=[answer for answer in answers if answer],
            data_gaps=gaps,
            source_turn_ids=[turn.turn_id for turn in turns],
        )
