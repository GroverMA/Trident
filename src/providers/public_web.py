"""Credential-free last-resort web discovery and page reading.

The paid search transport remains primary.  This provider exists so a temporary
credential or entitlement failure does not strand an already approved research
run.  Results still pass through the same evidence extraction and human review
gates as every other source.
"""

from __future__ import annotations

import html
import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

import requests

from src.models.evidence import CrawlResult, CrawledPage, SearchHit, WebSearchResult
from src.providers.base import ProviderError


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._ignored += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._ignored:
            self._ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored and data.strip():
            self.parts.append(data.strip())


class PublicWebProvider:
    """DuckDuckGo/Bing discovery plus guarded direct HTML retrieval."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout_seconds: int = 20,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout_seconds = min(max(timeout_seconds, 5), 30)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; TridentResearch/1.0; "
                "+https://trident-research.vercel.app)"
            )
        }

    def search_web(self, query: str) -> WebSearchResult:
        cleaned = query.strip()
        if not cleaned:
            raise ValueError("search query cannot be empty")
        errors: list[Exception] = []
        for search in (self._search_duckduckgo, self._search_bing):
            try:
                result = search(cleaned)
                if result.results:
                    return result
            except (requests.RequestException, ElementTree.ParseError, ValueError) as exc:
                errors.append(exc)
        raise ProviderError("Public web discovery failed") from (errors[-1] if errors else None)

    def _search_duckduckgo(self, query: str) -> WebSearchResult:
        response = self.session.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=self.headers,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        anchors = re.findall(
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            response.text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        snippets = re.findall(
            r'<(?:a|div)[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|div)>',
            response.text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        results: list[SearchHit] = []
        seen: set[str] = set()
        for index, (raw_url, raw_title) in enumerate(anchors):
            url = self._duckduckgo_target(html.unescape(raw_url))
            if not url or url in seen:
                continue
            self._require_public_url(url, resolve=False)
            results.append(
                SearchHit(
                    title=self._plain_text(raw_title) or "Untitled source",
                    url=url,
                    content=self._plain_text(snippets[index] if index < len(snippets) else "")[:1200],
                    domain=urlparse(url).netloc.lower(),
                )
            )
            seen.add(url)
            if len(results) >= 10:
                break
        return WebSearchResult(query=query, results=results, engine="duckduckgo-html")

    def _search_bing(self, query: str) -> WebSearchResult:
        try:
            response = self.session.get(
                "https://www.bing.com/search",
                params={"q": query, "format": "rss", "count": "10"},
                headers=self.headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
        except (requests.RequestException, ElementTree.ParseError):
            raise

        results: list[SearchHit] = []
        seen: set[str] = set()
        for item in root.findall(".//item"):
            url = (item.findtext("link") or "").strip()
            if not url or url in seen:
                continue
            try:
                self._require_public_url(url, resolve=False)
                results.append(
                    SearchHit(
                        title=(item.findtext("title") or "Untitled source").strip(),
                        url=url,
                        content=self._plain_text(item.findtext("description") or "")[:1200],
                        domain=urlparse(url).netloc.lower(),
                    )
                )
            except (ValueError, OSError):
                continue
            seen.add(url)
        return WebSearchResult(query=query, results=results, engine="bing-rss")

    def crawl_page(self, url: str) -> CrawlResult:
        try:
            self._require_public_url(url, resolve=True)
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.timeout_seconds,
                allow_redirects=True,
                stream=True,
            )
            response.raise_for_status()
            self._require_public_url(response.url, resolve=True)
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" not in content_type and "text/plain" not in content_type:
                raise ProviderError("Public page is not HTML or plain text")
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_content(chunk_size=64_000):
                if not chunk:
                    continue
                remaining = 2_000_000 - size
                chunks.append(chunk[:remaining])
                size += min(len(chunk), remaining)
                if size >= 2_000_000:
                    break
            body = b"".join(chunks)
            text = body.decode(response.encoding or "utf-8", errors="replace")
            if "html" in content_type:
                parser = _VisibleTextParser()
                parser.feed(text)
                text = "\n".join(parser.parts)
            text = re.sub(r"[ \t\r\f\v]+", " ", html.unescape(text))
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            if len(text) < 120:
                raise ProviderError("Public page returned insufficient readable text")
            return CrawlResult(
                pages=[CrawledPage(url=response.url, raw_content=text[:80_000])],
                engine="direct-http",
            )
        except ProviderError:
            raise
        except requests.RequestException as exc:
            raise ProviderError("Public page retrieval failed") from exc
        except (OSError, ValueError) as exc:
            raise ProviderError("Public page URL is not allowed") from exc

    @staticmethod
    def _plain_text(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value))).strip()

    @staticmethod
    def _duckduckgo_target(url: str) -> str:
        if url.startswith("//"):
            url = f"https:{url}"
        parsed = urlparse(url)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            return (parse_qs(parsed.query).get("uddg") or [""])[0]
        return url

    @staticmethod
    def _require_public_url(url: str, *, resolve: bool) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("URL must be absolute HTTP(S)")
        host = parsed.hostname.lower()
        if host == "localhost" or host.endswith(".local"):
            raise ValueError("Local URLs are not allowed")
        if not resolve:
            try:
                address = ipaddress.ip_address(host)
            except ValueError:
                return
            if not address.is_global:
                raise ValueError("Private addresses are not allowed")
            return
        for info in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM):
            address = ipaddress.ip_address(info[4][0])
            if not address.is_global:
                raise ValueError("Private addresses are not allowed")
