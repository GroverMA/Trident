from __future__ import annotations

import requests
import pytest

# Import the delivery boundary first, matching application startup order.  The
# services package re-exports planning services during initialization.
from src.api.app import app  # noqa: F401
from src.services.continuous_sensing import configure_sensing_subscription, ingest_internal_kpi, refresh_continuous_sensing
from src.services.sensing_review import (
    review_sensing_asset_draft,
    review_sensing_impact_task,
    review_sensing_revision_candidate,
    review_sensing_signal,
    update_sensing_inbox,
)
from src.models.sensing import AssetDraftGateStatus, CandidateGateStatus, ImpactReviewTaskStatus, InternalKpiObservation, SensingSourceDefinition, SignalReviewStatus
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

OFFICIAL_HTML = b"""<!doctype html><html><body>
<a href="/news/acme-approval">Acme Medical receives regulatory approval for new IVD platform</a>
<a href="/about">About us</a>
</body></html>"""


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
    assert first.management_digest is not None
    assert first.management_digest.new_signal_count == 1
    assert first.subscription.last_run_status == "succeeded"

    updated = current.model_copy(update={"continuous_sensing_artifact": first})
    second = refresh_continuous_sensing(updated, http_get=lambda *args, **kwargs: FakeResponse())
    assert len(second.signals) == 1
    assert second.signals[0].signal_id == signal.signal_id
    assert second.artifact_id == first.artifact_id
    assert second.management_digest.new_signal_count == 0


def test_refresh_preserves_inbox_read_and_reviewer_metadata() -> None:
    current = project()
    first = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    accepted = update_sensing_inbox(
        current.model_copy(update={"continuous_sensing_artifact": first}),
        signal_ids=[first.signals[0].signal_id],
        status=SignalReviewStatus.ACCEPTED,
        reviewer="Research Ops",
    )
    refreshed = refresh_continuous_sensing(accepted, http_get=lambda *args, **kwargs: FakeResponse())
    signal = refreshed.signals[0]
    assert signal.is_read is True
    assert signal.read_at is not None
    assert signal.reviewed_by == "Research Ops"
    assert signal.review_status == "accepted"


def test_subscription_requires_automatic_cadence_and_preserves_schedule_on_refresh() -> None:
    current = project()
    with pytest.raises(ValueError, match="每日或每周"):
        configure_sensing_subscription(current, enabled=True, cadence="manual")
    subscribed = configure_sensing_subscription(current, enabled=True, cadence="daily")
    subscription = subscribed.continuous_sensing_artifact.subscription
    assert subscription.enabled is True
    assert subscription.cadence == "daily"
    assert subscription.next_run_at is not None
    refreshed = refresh_continuous_sensing(subscribed, http_get=lambda *args, **kwargs: FakeResponse())
    assert refreshed.subscription.enabled is True
    assert refreshed.subscription.cadence == "daily"
    assert refreshed.subscription.last_run_at is not None
    assert refreshed.subscription.next_run_at > refreshed.subscription.last_run_at


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


def test_registered_primary_source_tracks_health_and_signal_provenance() -> None:
    source = SensingSourceDefinition(
        source_id="official-acme",
        name="Acme Medical Official",
        source_type="company_official",
        tier=1,
        url="https://example.com/company-feed.xml",
    )
    artifact = refresh_continuous_sensing(
        project(),
        sources=[source],
        http_get=lambda *args, **kwargs: FakeResponse(),
    )
    registered = artifact.sources[0]
    assert registered.source_id == "official-acme"
    assert registered.status == "succeeded"
    assert registered.last_checked_at is not None
    signal = artifact.signals[0]
    assert signal.source_id == "official-acme"
    assert signal.source_type == "company_official"
    assert signal.source_tier == 1


def test_html_connector_extracts_matching_official_announcements() -> None:
    source = SensingSourceDefinition(
        source_id="official-html",
        name="Acme Medical Official",
        source_type="company_official",
        source_format="html",
        tier=1,
        url="https://example.com/news",
    )

    def html_or_rss(url: str, **kwargs: object) -> FakeResponse:
        return FakeResponse(OFFICIAL_HTML if url == "https://example.com/news" else RSS)

    artifact = refresh_continuous_sensing(project(), sources=[source], http_get=html_or_rss)
    official = next(item for item in artifact.signals if item.source_id == "official-html")
    assert str(official.url) == "https://example.com/news/acme-approval"
    assert official.source_type == "company_official"
    assert official.source_tier == 1


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


def test_inbox_can_mark_selected_signals_read_without_reviewing_them() -> None:
    current = project()
    artifact = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    current = current.model_copy(update={"continuous_sensing_artifact": artifact})
    signal_id = artifact.signals[0].signal_id
    updated = update_sensing_inbox(current, signal_ids=[signal_id])
    signal = updated.continuous_sensing_artifact.signals[0]
    assert signal.is_read is True
    assert signal.read_at is not None
    assert signal.review_status == "needs_review"
    assert updated.enterprise_timeline_events == []


def test_batch_acceptance_records_reviewer_and_creates_one_task_per_signal() -> None:
    current = project()
    artifact = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    first = artifact.signals[0]
    second = first.model_copy(update={"signal_id": "second-signal", "title": "Acme Medical customer demand changes"})
    artifact = artifact.model_copy(update={"signals": [first, second]})
    current = current.model_copy(update={"continuous_sensing_artifact": artifact})
    updated = update_sensing_inbox(
        current,
        signal_ids=[first.signal_id, second.signal_id],
        status=SignalReviewStatus.ACCEPTED,
        note="进入本周管理层复核",
        reviewer="Research Ops",
    )
    assert all(signal.is_read for signal in updated.continuous_sensing_artifact.signals)
    assert all(signal.review_status == "accepted" for signal in updated.continuous_sensing_artifact.signals)
    assert all(signal.reviewed_by == "Research Ops" for signal in updated.continuous_sensing_artifact.signals)
    assert len(updated.continuous_sensing_artifact.review_tasks) == 2
    assert len(updated.enterprise_timeline_events) == 2


def test_internal_kpi_becomes_high_impact_governed_operations_signal() -> None:
    observation = InternalKpiObservation(
        metric_name="月度订单额",
        value=70,
        unit="万元",
        period="2026-08",
        comparison_value=95,
        target_value=100,
        note="两个核心客户延期",
    )
    updated = ingest_internal_kpi(project(), observation)
    signal = updated.continuous_sensing_artifact.signals[0]
    assert signal.signal_id.startswith("KPI-")
    assert str(signal.url) == "https://trident-research.vercel.app/sensing"
    assert signal.source_type == "internal_kpi"
    assert signal.category == "operations"
    assert signal.impact == "high"
    assert signal.review_status == "needs_review"
    assert signal.kpi_observation == observation
    assert updated.continuous_sensing_artifact.review_tasks == []


def test_internal_kpi_same_metric_and_period_updates_without_duplicate() -> None:
    first = ingest_internal_kpi(project(), InternalKpiObservation(
        metric_name="交付周期", value=18, unit="天", period="2026-W35", direction="lower_is_better", target_value=14,
    ))
    second = ingest_internal_kpi(first, InternalKpiObservation(
        metric_name="交付周期", value=16, unit="天", period="2026-W35", direction="lower_is_better", target_value=14,
    ))
    assert len(second.continuous_sensing_artifact.signals) == 1
    assert second.continuous_sensing_artifact.signals[0].kpi_observation.value == 16


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
    assert gated_task.candidate.asset_draft is not None
    assert gated_task.candidate.asset_draft.gate_status == "needs_review"
    assert gated_task.candidate.asset_draft.validation_checks
    assert gated.research_brief_artifact is accepted.research_brief_artifact
    assert gated.company_scorecard_artifact is accepted.company_scorecard_artifact
    assert gated.action_plan_artifact is accepted.action_plan_artifact
    assert gated.enterprise_timeline_events[-1].event_type == "sensing_candidate_approved"

    activated = review_sensing_asset_draft(
        gated,
        task_id=task.task_id,
        status=AssetDraftGateStatus.ACTIVATED,
        note="人工确认新范围版本",
    )
    activated_task = activated.continuous_sensing_artifact.review_tasks[0]
    assert activated_task.candidate.asset_draft.gate_status == "activated"
    assert activated.research_brief_artifact is not None
    assert activated.research_brief_artifact.human_confirmed is True
    assert activated.research_brief_artifact.artifact_id == activated_task.candidate.asset_draft.proposed_artifact_id
    assert activated.research_brief_history == []
    assert activated.enterprise_timeline_events[-1].event_type == "sensing_asset_activated"


def test_asset_gate_rejection_keeps_current_asset_unchanged() -> None:
    current = project()
    artifact = refresh_continuous_sensing(current, http_get=lambda *args, **kwargs: FakeResponse())
    accepted = review_sensing_signal(
        current.model_copy(update={"continuous_sensing_artifact": artifact}),
        signal_id=artifact.signals[0].signal_id,
        status=SignalReviewStatus.ACCEPTED,
    )
    task = accepted.continuous_sensing_artifact.review_tasks[0]
    candidate = review_sensing_impact_task(
        accepted,
        task_id=task.task_id,
        status=ImpactReviewTaskStatus.APPROVED_FOR_REVISION,
    )
    draft = review_sensing_revision_candidate(
        candidate,
        task_id=task.task_id,
        status=CandidateGateStatus.APPROVED,
    )
    rejected = review_sensing_asset_draft(
        draft,
        task_id=task.task_id,
        status=AssetDraftGateStatus.REJECTED,
    )
    assert rejected.research_brief_artifact is None
    assert rejected.continuous_sensing_artifact.review_tasks[0].candidate.asset_draft.gate_status == "rejected"


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
