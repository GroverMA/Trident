from __future__ import annotations

import requests
import pytest

# Import the delivery boundary first, matching application startup order.  The
# services package re-exports planning services during initialization.
from src.api.app import app  # noqa: F401
from src.services.continuous_sensing import refresh_continuous_sensing
from src.services.sensing_review import (
    review_sensing_impact_task,
    review_sensing_revision_candidate,
    review_sensing_signal,
)
from src.models.sensing import CandidateGateStatus, ImpactReviewTaskStatus, SignalReviewStatus
from src.state.project import ProjectState


RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item>
    <title>Acme Medical receives regulatory approval for new IVD platform</title>
    <link>https://example.com/acme-approval</link>
    <description>Acme Medical expands its IVD diagnostics portfolio in China.</description>
    <pubDate>Mon, 24 Aug 2026 08:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Unrelated consumer story</title>
    <link>https://example.com/unrelated</link>
    <description>No monitored entities are mentioned.</description>
  </item>
</channel></rss>"""

NOISY_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item>
    <title>China consumer confidence update</title>
    <link>https://example.com/china-only</link>
    <description>China macroeconomic news unrelated to diagnostics.</description>
    <pubDate>Mon, 24 Aug 2026 08:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Acme Medical opens a new diagnostics facility</title>
    <link>https://example.com/acme-new</link>
    <description>Acme Medical expands IVD diagnostics capacity in China.</description>
    <source>Healthcare Daily</source>
    <pubDate>Mon, 24 Aug 2026 08:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Acme Medical legacy announcement</title>
    <link>https://example.com/acme-old</link>
    <description>Acme Medical historic update.</description>
    <pubDate>Mon, 24 Aug 2020 08:00:00 GMT</pubDate>
  </item>
</channel></rss>"""


class FakeResponse:
    def __init__(self, content: bytes = RSS, *, fails: bool = False) -> None:
        self.content = content
        self.fails = fails

    def raise_for_status(self) -> None:
        if self.fails:
            raise requests.HTTPError("unavailable")


def project() -> ProjectState:
    return ProjectState(
        project_name="Acme China IVD monitoring",
        industry="IVD diagnostics",
        region="China",
        target_company="Acme Medical",
        research_objective="Monitor company and industry changes",
        time_horizon="2026-2030",
    )


def test_refresh_fetches_filters_classifies_and_deduplicates() -> None:
    current = project()
    first = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    assert len(first.signals) == 1
    signal = first.signals[0]
    assert signal.title.startswith("Acme Medical")
    assert signal.impact == "high"
    assert "Acme Medical" in signal.matched_terms
    assert signal.source == "Google News"

    updated = current.model_copy(update={"continuous_sensing_artifact": first})
    second = refresh_continuous_sensing(updated, http_get=lambda *args, **kwargs: FakeResponse())
    assert len(second.signals) == 1
    assert second.signals[0].signal_id == signal.signal_id
    assert second.artifact_id == first.artifact_id


def test_refresh_records_source_failure_without_losing_previous_signals() -> None:
    current = project()
    first = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    updated = current.model_copy(update={"continuous_sensing_artifact": first})
    failed = refresh_continuous_sensing(updated, http_get=lambda *args, **kwargs: FakeResponse(fails=True))
    assert len(failed.signals) == 1
    assert failed.fetch_errors == ["Google News: HTTPError"]


def test_refresh_rejects_region_only_noise_and_stale_items_and_keeps_publisher() -> None:
    artifact = refresh_continuous_sensing(
        project(),
        http_get=lambda *args, **kwargs: FakeResponse(NOISY_RSS),
    )
    assert len(artifact.signals) == 1
    assert artifact.signals[0].title.startswith("Acme Medical opens")
    assert artifact.signals[0].source == "Healthcare Daily"
    assert artifact.signals[0].relevance_score >= 70


def test_refresh_uses_separate_company_and_industry_queries_with_recency() -> None:
    urls: list[str] = []

    def capture(url: str, **kwargs: object) -> FakeResponse:
        urls.append(url)
        return FakeResponse()

    refresh_continuous_sensing(project(), http_get=capture)
    assert len(urls) == 2
    assert all("when%3A180d" in url for url in urls)
    assert any("Acme+Medical" in url for url in urls)
    assert any("IVD+diagnostics" in url for url in urls)


def test_refresh_rejects_private_or_insecure_custom_feeds() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        refresh_continuous_sensing(project(), feed_urls=["http://example.com/feed"])
    with pytest.raises(ValueError, match="私网"):
        refresh_continuous_sensing(project(), feed_urls=["https://127.0.0.1/feed"])


def test_human_acceptance_creates_assessment_and_timeline_without_replacing_plan() -> None:
    current = project()
    artifact = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    current = current.model_copy(update={"continuous_sensing_artifact": artifact})
    signal_id = artifact.signals[0].signal_id
    reviewed = review_sensing_signal(current, signal_id=signal_id, status=SignalReviewStatus.ACCEPTED)
    signal = reviewed.continuous_sensing_artifact.signals[0]
    assert signal.review_status == "accepted"
    assert signal.assessment is not None
    assert "research_scope" in signal.assessment.affected_assets
    assert reviewed.action_plan_artifact is current.action_plan_artifact
    assert reviewed.enterprise_timeline_events[-1].event_type == "sensing_signal_accepted"
    assert len(reviewed.continuous_sensing_artifact.review_tasks) == 1
    task = reviewed.continuous_sensing_artifact.review_tasks[0]
    assert task.target == "research_scope"
    assert task.status == "needs_review"

    repeated = review_sensing_signal(reviewed, signal_id=signal_id, status=SignalReviewStatus.ACCEPTED)
    assert len(repeated.enterprise_timeline_events) == 1
    assert len(repeated.continuous_sensing_artifact.review_tasks) == 1


def test_human_ignore_does_not_create_impact_or_timeline() -> None:
    current = project()
    artifact = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    current = current.model_copy(update={"continuous_sensing_artifact": artifact})
    reviewed = review_sensing_signal(current, signal_id=artifact.signals[0].signal_id, status=SignalReviewStatus.IGNORED)
    assert reviewed.continuous_sensing_artifact.signals[0].assessment is None
    assert reviewed.enterprise_timeline_events == []
    assert reviewed.continuous_sensing_artifact.review_tasks == []


def test_impact_task_approval_authorizes_candidate_but_does_not_replace_assets() -> None:
    current = project()
    artifact = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    accepted = review_sensing_signal(
        current.model_copy(update={"continuous_sensing_artifact": artifact}),
        signal_id=artifact.signals[0].signal_id,
        status=SignalReviewStatus.ACCEPTED,
    )
    task = accepted.continuous_sensing_artifact.review_tasks[0]
    reviewed = review_sensing_impact_task(
        accepted,
        task_id=task.task_id,
        status=ImpactReviewTaskStatus.APPROVED_FOR_REVISION,
        note="进入下一轮研究范围复核",
    )
    updated = reviewed.continuous_sensing_artifact.review_tasks[0]
    assert updated.status == "approved_for_revision"
    assert updated.candidate is not None
    assert updated.candidate.gate_status == "needs_review"
    assert updated.candidate.scenario_id == accepted.scenario_pack
    assert updated.candidate.evidence_signal_ids == [task.signal_id]
    assert updated.candidate.proposed_changes
    assert "defining-industry-markets" in updated.candidate.skill_versions
    assert reviewed.research_brief_artifact is accepted.research_brief_artifact
    assert reviewed.company_scorecard_artifact is accepted.company_scorecard_artifact
    assert reviewed.action_plan_artifact is accepted.action_plan_artifact
    assert reviewed.enterprise_timeline_events[-1].event_type == "sensing_revision_authorized"

    gated = review_sensing_revision_candidate(
        reviewed,
        task_id=task.task_id,
        status=CandidateGateStatus.APPROVED,
        note="同意进入后续研究范围再生成",
    )
    gated_task = gated.continuous_sensing_artifact.review_tasks[0]
    assert gated_task.candidate.gate_status == "approved"
    assert gated.research_brief_artifact is accepted.research_brief_artifact
    assert gated.company_scorecard_artifact is accepted.company_scorecard_artifact
    assert gated.action_plan_artifact is accepted.action_plan_artifact
    assert gated.enterprise_timeline_events[-1].event_type == "sensing_candidate_approved"


def test_candidate_gate_requires_generated_candidate() -> None:
    current = project()
    artifact = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    accepted = review_sensing_signal(
        current.model_copy(update={"continuous_sensing_artifact": artifact}),
        signal_id=artifact.signals[0].signal_id,
        status=SignalReviewStatus.ACCEPTED,
    )
    with pytest.raises(ValueError, match="尚未生成候选版本"):
        review_sensing_revision_candidate(
            accepted,
            task_id=accepted.continuous_sensing_artifact.review_tasks[0].task_id,
            status=CandidateGateStatus.APPROVED,
        )
