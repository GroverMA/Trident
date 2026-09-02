"""Fetch, normalize and rank project-specific public news signals."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import ipaddress
import os
import re
from urllib.parse import quote_plus, urljoin, urlparse
import xml.etree.ElementTree as ET

import requests

from src.models.sensing import (
    ContinuousSensingArtifact,
    SensingSignal,
    SignalCategory,
    SignalImpact,
    SensingCadence,
    SensingManagementDigest,
    SensingRunStatus,
    SensingSourceDefinition,
    SensingSourceFormat,
    SensingSourceStatus,
    SensingSourceType,
    SensingSubscription,
)
from src.state.project import ProjectState


_TAG_RE = re.compile(r"<[^>]+>")
_CATEGORY_TERMS = {
    SignalCategory.POLICY: ("政策", "监管", "法规", "许可", "审批", "regulation", "policy"),
    SignalCategory.COMPETITION: ("竞争", "新品", "发布", "合作", "收购", "融资", "competitor", "launch"),
    SignalCategory.CUSTOMER: ("客户", "采购", "需求", "订单", "招标", "customer", "demand", "procurement"),
    SignalCategory.TECHNOLOGY: ("技术", "专利", "研发", "临床", "创新", "technology", "patent", "clinical"),
    SignalCategory.OPERATIONS: ("营收", "利润", "业绩", "产能", "供应链", "revenue", "profit", "capacity"),
}
_HIGH_IMPACT_TERMS = ("监管", "禁令", "召回", "收购", "破产", "获批", "审批", "重大", "ban", "recall", "acquisition", "regulatory", "approval")
_DEFAULT_MAX_AGE_DAYS = 180


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._href = next((value for key, value in attrs if key.lower() == "href" and value), None)
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            text = _clean(" ".join(self._text))
            if text:
                self.links.append((text, self._href))
            self._href = None
            self._text = []


def _source_items(source: SensingSourceDefinition, content: bytes) -> list[tuple[str, str, str, datetime | None, str | None]]:
    stripped = content.lstrip().lower()
    use_html = source.source_format == SensingSourceFormat.HTML or (
        source.source_format == SensingSourceFormat.AUTO
        and not (stripped.startswith(b"<?xml") or stripped.startswith(b"<rss") or stripped.startswith(b"<feed"))
    )
    if use_html:
        parser = _LinkParser()
        parser.feed(content.decode("utf-8", errors="replace"))
        return [
            (title, urljoin(str(source.url), href), "", None, None)
            for title, href in parser.links[:100]
            if urlparse(urljoin(str(source.url), href)).scheme in {"http", "https"}
        ]
    root = ET.fromstring(content)
    return [
        (
            _clean(item.findtext("title")),
            _clean(item.findtext("link")),
            _clean(item.findtext("description")),
            _published(item.findtext("pubDate")),
            _clean(item.findtext("source")) or None,
        )
        for item in root.findall(".//item")[:50]
    ]


def _next_run(cadence: SensingCadence, now: datetime) -> datetime | None:
    if cadence == SensingCadence.DAILY:
        return now + timedelta(days=1)
    if cadence == SensingCadence.WEEKLY:
        return now + timedelta(days=7)
    return None


def configure_sensing_subscription(
    project: ProjectState,
    *,
    enabled: bool,
    cadence: SensingCadence,
) -> ProjectState:
    if enabled and cadence == SensingCadence.MANUAL:
        raise ValueError("启用自动感知时必须选择每日或每周频率")
    now = datetime.now(UTC)
    previous = project.continuous_sensing_artifact
    artifact = previous or ContinuousSensingArtifact(
        project_id=project.project_id,
        watch_terms=default_watch_terms(project),
    )
    subscription = SensingSubscription(
        enabled=enabled,
        cadence=cadence,
        next_run_at=_next_run(cadence, now) if enabled else None,
        last_run_at=artifact.subscription.last_run_at,
        last_run_status=artifact.subscription.last_run_status,
        last_run_error=artifact.subscription.last_run_error,
    )
    return project.model_copy(update={
        "continuous_sensing_artifact": artifact.model_copy(update={"subscription": subscription}),
        "updated_at": now,
    })


def _digest(signals: list[SensingSignal], previous_ids: set[str]) -> SensingManagementDigest:
    new_signals = [item for item in signals if item.signal_id not in previous_ids]
    high = [item for item in signals if item.impact == SignalImpact.HIGH and item.review_status == "needs_review"]
    pending = [item for item in signals if item.review_status == "needs_review"]
    headline = f"新增 {len(new_signals)} 条信号，{len(high)} 条高影响待复核"
    top = (high or new_signals or pending)[:5]
    summary = "；".join(item.title for item in top) or "本轮未发现新的匹配信号"
    return SensingManagementDigest(
        headline=headline,
        summary=summary,
        high_impact_count=len(high),
        pending_review_count=len(pending),
        new_signal_count=len(new_signals),
        top_signal_ids=[item.signal_id for item in top],
    )


def default_watch_terms(project: ProjectState) -> list[str]:
    candidates = [project.target_company, project.industry, project.region]
    if project.research_brief_artifact:
        candidates.extend(project.research_brief_artifact.market_definition.inclusions[:3])
    return list(dict.fromkeys(term.strip() for term in candidates if term and term.strip()))


def _clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", unescape(_TAG_RE.sub(" ", value or ""))).strip()


def _published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (TypeError, ValueError, OverflowError):
        return None


def _classify(text: str) -> SignalCategory:
    lowered = text.lower()
    scores = {category: sum(term.lower() in lowered for term in terms) for category, terms in _CATEGORY_TERMS.items()}
    category, score = max(scores.items(), key=lambda item: item[1])
    return category if score else SignalCategory.OTHER


def _rank(
    text: str,
    watch_terms: list[str],
    *,
    anchor_terms: list[str],
    published_at: datetime | None,
) -> tuple[list[str], int, SignalImpact, str]:
    lowered = text.lower()
    matched = [term for term in watch_terms if term.lower() in lowered]
    matched_anchors = [term for term in anchor_terms if term.lower() in lowered]
    if not matched_anchors:
        return matched, 0, SignalImpact.REVIEW, "仅命中地区或宽泛检索词，未关联企业、行业或关注主题"
    freshness = 10 if published_at and published_at >= datetime.now(UTC) - timedelta(days=30) else 0
    company_bonus = 20 if watch_terms and watch_terms[0].lower() in lowered else 0
    relevance = min(100, 35 + len(matched_anchors) * 20 + min(10, len(matched) * 5) + company_bonus + freshness)
    material = any(term.lower() in lowered for term in _HIGH_IMPACT_TERMS)
    if material and matched_anchors:
        return matched, relevance, SignalImpact.HIGH, "命中关注实体，并包含监管、交易或重大经营变化词"
    if matched_anchors:
        return matched, relevance, SignalImpact.MEDIUM, "与当前企业、行业或地区关注词直接相关"
    return matched, relevance, SignalImpact.REVIEW, "来源命中检索式，但仍需人工判断与项目的关系"


def _rss_sources(
    project: ProjectState,
    watch_terms: list[str],
    custom_sources: list[SensingSourceDefinition],
    max_age_days: int,
) -> list[SensingSourceDefinition]:
    recency = f"when:{max_age_days}d"
    queries: list[str] = []
    if project.target_company:
        queries.append(f'"{project.target_company.strip()}" {recency}')
    if project.industry:
        industry_query = " ".join(term for term in [project.industry.strip(), project.region.strip(), recency] if term)
        queries.append(industry_query)
    extra_terms = [term for term in watch_terms if term not in {project.target_company, project.industry, project.region}]
    queries.extend(f'"{term}" {recency}' for term in extra_terms[:5])
    defaults = [SensingSourceDefinition(
        source_id=f"google-news-{sha256(query.encode()).hexdigest()[:10]}",
        name="Google News",
        source_type=SensingSourceType.NEWS_AGGREGATOR,
        tier=3,
        url=f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    )
        for query in dict.fromkeys(queries)
    ]
    configured = [_safe_feed_url(url.strip()) for url in os.getenv("TRIDENT_SENSING_RSS_URLS", "").split(",") if url.strip()]
    env_sources = [SensingSourceDefinition(
        name="部署环境 RSS",
        source_type=SensingSourceType.PROFESSIONAL_MEDIA,
        tier=2,
        url=url,
    ) for url in configured]
    return [*defaults, *env_sources, *(source for source in custom_sources if source.enabled)]


def _safe_feed_url(url: str) -> str:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not hostname or hostname in {"localhost", "localhost.localdomain"}:
        raise ValueError("自定义 RSS 必须使用可公开访问的 HTTPS 地址")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise ValueError("自定义 RSS 不得指向本机、私网或保留地址")
    return url


def refresh_continuous_sensing(
    project: ProjectState,
    *,
    watch_terms: list[str] | None = None,
    feed_urls: list[str] | None = None,
    sources: list[SensingSourceDefinition] | None = None,
    http_get=requests.get,
) -> ContinuousSensingArtifact:
    terms = list(dict.fromkeys(term.strip() for term in (watch_terms or default_watch_terms(project)) if term.strip()))
    if not terms:
        raise ValueError("持续感知至少需要一个公司、行业或主题关注词")
    custom_urls = list(dict.fromkeys(_safe_feed_url(url.strip()) for url in (feed_urls or []) if url.strip()))
    previous = project.continuous_sensing_artifact
    custom_sources = list(sources if sources is not None else (previous.sources if previous else []))
    known_urls = {str(source.url) for source in custom_sources}
    custom_sources.extend(SensingSourceDefinition(
        name="自定义 RSS",
        source_type=SensingSourceType.PROFESSIONAL_MEDIA,
        tier=2,
        url=url,
    ) for url in custom_urls if url not in known_urls)
    for source in custom_sources:
        _safe_feed_url(str(source.url))
    try:
        max_age_days = max(1, int(os.getenv("TRIDENT_SENSING_MAX_AGE_DAYS", str(_DEFAULT_MAX_AGE_DAYS))))
    except ValueError:
        max_age_days = _DEFAULT_MAX_AGE_DAYS
    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    anchor_terms = [term for term in terms if term.casefold() != (project.region or "").strip().casefold()]
    previous_ids = {item.signal_id for item in previous.signals} if previous else set()
    by_id = {
        item.signal_id: item
        for item in (previous.signals if previous else [])
        if item.review_status == "accepted" or not item.published_at or item.published_at >= cutoff
    }
    title_ids = {re.sub(r"\W+", "", item.title).casefold(): item.signal_id for item in by_id.values()}
    errors: list[str] = []

    source_results: dict[str, SensingSourceDefinition] = {source.source_id: source for source in custom_sources}
    for source in _rss_sources(project, terms, custom_sources, max_age_days):
        try:
            response = http_get(str(source.url), timeout=10, headers={"User-Agent": "TridentResearch/1.0"})
            response.raise_for_status()
            for title, link, summary, published_at, item_source in _source_items(source, response.content):
                if not title or not link:
                    continue
                if published_at and published_at < cutoff:
                    continue
                matched, score, impact, reason = _rank(
                    f"{title} {summary}",
                    terms,
                    anchor_terms=anchor_terms,
                    published_at=published_at,
                )
                if score == 0:
                    continue
                title_key = re.sub(r"\W+", "", title).casefold()
                signal_id = title_ids.get(title_key) or sha256(title_key.encode("utf-8")).hexdigest()[:24]
                title_ids[title_key] = signal_id
                publisher = item_source or source.name
                by_id[signal_id] = SensingSignal(
                    signal_id=signal_id,
                    title=title,
                    summary=summary[:600],
                    url=link,
                    source=publisher,
                    source_id=source.source_id,
                    source_type=source.source_type,
                    source_tier=source.tier,
                    published_at=published_at,
                    category=_classify(f"{title} {summary}"),
                    impact=impact,
                    impact_reason=reason,
                    matched_terms=matched,
                    relevance_score=score,
                    project_id=project.project_id,
                    review_status=by_id[signal_id].review_status if signal_id in by_id else "needs_review",
                    reviewer_note=by_id[signal_id].reviewer_note if signal_id in by_id else None,
                    reviewed_at=by_id[signal_id].reviewed_at if signal_id in by_id else None,
                    assessment=by_id[signal_id].assessment if signal_id in by_id else None,
                )
            if source.source_id in source_results:
                source_results[source.source_id] = source.model_copy(update={
                    "status": SensingSourceStatus.SUCCEEDED,
                    "last_checked_at": datetime.now(UTC),
                    "last_error": None,
                })
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            error = f"{source.name}: {type(exc).__name__}"
            if error not in errors:
                errors.append(error)
            if source.source_id in source_results:
                source_results[source.source_id] = source.model_copy(update={
                    "status": SensingSourceStatus.FAILED,
                    "last_checked_at": datetime.now(UTC),
                    "last_error": type(exc).__name__,
                })

    signals = sorted(
        by_id.values(),
        key=lambda item: (item.source_tier == 1, item.relevance_score, item.published_at or item.captured_at),
        reverse=True,
    )[:200]
    now = datetime.now(UTC)
    prior_subscription = previous.subscription if previous else SensingSubscription()
    run_status = SensingRunStatus.PARTIAL if errors else SensingRunStatus.SUCCEEDED
    subscription = prior_subscription.model_copy(update={
        "last_run_at": now,
        "last_run_status": run_status,
        "last_run_error": "；".join(errors) or None,
        "next_run_at": _next_run(prior_subscription.cadence, now) if prior_subscription.enabled else None,
    })
    payload = dict(
        project_id=project.project_id,
        watch_terms=terms,
        feed_urls=custom_urls,
        sources=list(source_results.values()),
        signals=signals,
        review_tasks=list(previous.review_tasks) if previous else [],
        subscription=subscription,
        management_digest=_digest(signals, previous_ids),
        fetch_errors=errors,
    )
    if previous:
        payload["artifact_id"] = previous.artifact_id
    return ContinuousSensingArtifact(**payload)
