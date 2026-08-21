"""Scenario-pack-driven adaptive interview orchestration.

The service contains no PE/VC/growth branches.  All scenario differences are
declared by the registered pack, while session state is stored on ProjectState.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Callable, Protocol

from src.config import ConfigurationError
from src.core.registry import ExtensionRegistry
from src.models.interview import (
    EntityProfileArtifact,
    InterviewAnswerAnalysis,
    InterviewStatus,
    InterviewTurn,
    ScenarioInterviewArtifact,
)
from src.providers.base import ChatMessage, ProviderError
from src.state.project import ProjectState


class ScenarioInterviewError(ValueError):
    pass


class StructuredInterviewModel(Protocol):
    def complete_json(
        self, messages: list[ChatMessage], *, enable_thinking: bool = False
    ) -> tuple[dict, object]: ...


class ScenarioInterviewService:
    def __init__(
        self,
        packs: ExtensionRegistry,
        *,
        model_factory: Callable[[], StructuredInterviewModel] | None = None,
    ) -> None:
        self._packs = packs
        self._model_factory = model_factory

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
        analysis, provider_warning = self._analyse_answer(project, session, current, text)
        quality = analysis.answer_quality
        turns = [
            turn.model_copy(update={"answer": text, "answer_quality": quality, "analysis": analysis})
            if turn.turn_id == current.turn_id else turn
            for turn in session.turns
        ]
        followups_for_topic = sum(1 for turn in turns if turn.topic_id == current.topic_id) - 1
        can_follow_up = (
            not analysis.topic_complete
            and bool(analysis.follow_up_question)
            and followups_for_topic < 2
            and len(turns) < session.max_turns
        )
        if can_follow_up:
            turns.append(InterviewTurn(topic_id=current.topic_id, question=str(analysis.follow_up_question)))
            covered = list(session.covered_topics)
            remaining = list(session.remaining_topics)
        else:
            covered = list(dict.fromkeys([*session.covered_topics, current.topic_id]))
            remaining = [topic for topic in session.remaining_topics if topic != current.topic_id]
        policy = self._policy(project)
        questions = [str(item) for item in policy.get("starter_questions", [])]
        topics = [str(item) for item in policy.get("diagnostic_topics", [])]
        if len(topics) != len(questions):
            topics = [f"topic_{index + 1}" for index in range(len(questions))]
        if can_follow_up:
            status = InterviewStatus.IN_PROGRESS
            profile = None
        elif remaining:
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
            "provider_warning": provider_warning,
            "updated_at": datetime.now(UTC),
        })
        return project.model_copy(update={"interview_session_artifact": updated, "entity_profile_artifact": profile})

    def _analyse_answer(
        self,
        project: ProjectState,
        session: ScenarioInterviewArtifact,
        current: InterviewTurn,
        answer: str,
    ) -> tuple[InterviewAnswerAnalysis, str | None]:
        if self._model_factory is not None:
            try:
                model = self._model_factory()
                payload, _ = model.complete_json(
                    [
                        ChatMessage(
                            role="system",
                            content=(
                                "你是企业决策诊断访谈分析器。必须只输出JSON。逐轮分析用户回答，"
                                "不得把意见或推测写成已验证事实。若答案含糊、矛盾或缺少对后续决策必要的信息，"
                                "只提出一个自然、容易回答的追问；若当前主题信息已足够，则topic_complete=true。"
                                "JSON字段必须包含summary, extracted_facts, ambiguities, missing_information, "
                                "answer_quality, topic_complete, follow_up_question, confidence。"
                            ),
                        ),
                        ChatMessage(
                            role="user",
                            content=json.dumps(
                                {
                                    "scenario": project.scenario_pack,
                                    "objective": session.objective,
                                    "topic": current.topic_id,
                                    "question": current.question,
                                    "answer": answer,
                                    "previous_turns": [
                                        {"topic": turn.topic_id, "question": turn.question, "answer": turn.answer}
                                        for turn in session.turns[:-1]
                                    ],
                                },
                                ensure_ascii=False,
                            ),
                        ),
                    ],
                    enable_thinking=False,
                )
                analysis = InterviewAnswerAnalysis.model_validate(payload)
                if not analysis.topic_complete and not analysis.follow_up_question:
                    analysis = analysis.model_copy(update={"follow_up_question": self._fallback_question(answer)})
                return analysis, None
            except (ConfigurationError, ProviderError, ValueError, TypeError, KeyError) as exc:
                warning = f"AI分析暂时降级，回答已安全保存（{type(exc).__name__}）"
                return self._fallback_analysis(answer), warning
        return self._fallback_analysis(answer), None

    @classmethod
    def _fallback_analysis(cls, answer: str) -> InterviewAnswerAnalysis:
        vague_terms = ("不知道", "不清楚", "大概", "可能", "差不多", "应该", "没有数据")
        vague = len(answer) < 12 or any(term in answer for term in vague_terms)
        return InterviewAnswerAnalysis(
            summary=answer[:160],
            extracted_facts=[answer] if not vague else [],
            ambiguities=["回答仍需要口径、范围或实例支持"] if vague else [],
            missing_information=["可验证的数据、范围或具体案例"] if vague else [],
            answer_quality="needs_validation" if vague else "sufficient",
            topic_complete=not vague,
            follow_up_question=cls._fallback_question(answer) if vague else None,
            confidence=0.35 if vague else 0.65,
        )

    @staticmethod
    def _fallback_question(answer: str) -> str:
        return "你能再补充一个具体范围、变化方向或真实例子吗？如果没有数据，也可以说明这个判断来自谁和什么现象。"

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
