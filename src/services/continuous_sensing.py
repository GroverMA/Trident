"""Fetch, normalize and rank project-specific public news signals."""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
import ipaddress
import os
import re
from urllib.parse import quote_plus, urlparse
import xml.etree.ElementTree as ET

import requests

from src.models.sensing import (
    ContinuousSensingArtifact,
    SensingSignal,
    SignalCategory,
    SignalImpact,
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


def _rank(text: str, watch_terms: list[str]) -> tuple[list[str], int, SignalImpact, str]:
    lowered = text.lower()
    matched = [term for term in watch_terms if term.lower() in lowered]
    relevance = min(100, 25 + len(matched) * 25 + (15 if matched and watch_terms[0] in matched else 0)) if matched else 15
    material = any(term.lower() in lowered for term in _HIGH_IMPACT_TERMS)
    if material and matched:
        return matched, relevance, SignalImpact.HIGH, "命中关注实体，并包含监管、交易或重大经营变化词"
    if matched:
        return matched, relevance, SignalImpact.MEDIUM, "与当前企业、行业或地区关注词直接相关"
    return matched, relevance, SignalImpact.REVIEW, "来源命中检索式，但仍需人工判断与项目的关系"


def _rss_urls(watch_terms: list[str], custom_urls: list[str]) -> list[tuple[str, str]]:
    query = " ".join(watch_terms[:5])
    defaults = [
        ("Google News", f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ]
    configured = [_safe_feed_url(url.strip()) for url in os.getenv("TRIDENT_SENSING_RSS_URLS", "").split(",") if url.strip()]
    return [*defaults, *(("自定义 RSS", url) for url in [*configured, *custom_urls])]


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
    http_get=requests.get,
) -> ContinuousSensingArtifact:
    terms = list(dict.fromkeys(term.strip() for term in (watch_terms or default_watch_terms(project)) if term.strip()))
    if not terms:
        raise ValueError("持续感知至少需要一个公司、行业或主题关注词")
    custom_urls = list(dict.fromkeys(_safe_feed_url(url.strip()) for url in (feed_urls or []) if url.strip()))
    previous = project.continuous_sensing_artifact
    by_id = {item.signal_id: item for item in (previous.signals if previous else [])}
    errors: list[str] = []

    for source_name, url in _rss_urls(terms, custom_urls):
        try:
            response = http_get(url, timeout=10, headers={"User-Agent": "TridentResearch/1.0"})
            response.raise_for_status()
            root = ET.fromstring(response.content)
            for item in root.findall(".//item")[:50]:
                title = _clean(item.findtext("title"))
                link = _clean(item.findtext("link"))
                if not title or not link:
                    continue
                summary = _clean(item.findtext("description"))
                matched, score, impact, reason = _rank(f"{title} {summary}", terms)
                if not matched:
                    continue
                signal_id = sha256(link.encode("utf-8")).hexdigest()[:24]
                by_id[signal_id] = SensingSignal(
                    signal_id=signal_id,
                    title=title,
                    summary=summary[:600],
                    url=link,
                    source=source_name,
                    published_at=_published(item.findtext("pubDate")),
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
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            errors.append(f"{source_name}: {type(exc).__name__}")

    signals = sorted(
        by_id.values(),
        key=lambda item: (item.published_at or item.captured_at, item.relevance_score),
        reverse=True,
    )[:200]
    payload = dict(
        project_id=project.project_id,
        watch_terms=terms,
        feed_urls=custom_urls,
        signals=signals,
        fetch_errors=errors,
    )
    if previous:
        payload["artifact_id"] = previous.artifact_id
    return ContinuousSensingArtifact(**payload)
