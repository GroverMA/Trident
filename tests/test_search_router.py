from __future__ import annotations

import asyncio

from src.models.evidence import CrawlResult, WebSearchResult
from src.providers.base import ProviderError
from src.providers.search_router import SearchRouter


class FakeMCP:
    def __init__(self, *, fail: bool) -> None:
        self.fail = fail
        self.search_calls = 0
        self.crawl_calls = 0

    async def search_web(self, query: str) -> WebSearchResult:
        self.search_calls += 1
        if self.fail:
            raise ProviderError("MCP unavailable")
        return WebSearchResult(query=query)

    async def crawl_page(self, url: str) -> CrawlResult:
        self.crawl_calls += 1
        if self.fail:
            raise ProviderError("MCP unavailable")
        return CrawlResult()


class FakeRest:
    def __init__(self) -> None:
        self.search_calls = 0
        self.crawl_calls = 0

    def search_web(self, query: str) -> WebSearchResult:
        self.search_calls += 1
        return WebSearchResult(query=query)

    def crawl_page(self, url: str) -> CrawlResult:
        self.crawl_calls += 1
        return CrawlResult()


class FakePublic:
    def __init__(self) -> None:
        self.search_calls = 0
        self.crawl_calls = 0

    def search_web(self, query: str) -> WebSearchResult:
        self.search_calls += 1
        return WebSearchResult(query=query, engine="public-test")

    def crawl_page(self, url: str) -> CrawlResult:
        self.crawl_calls += 1
        return CrawlResult(engine="public-test")


class FailingRest(FakeRest):
    def search_web(self, query: str) -> WebSearchResult:
        self.search_calls += 1
        raise ProviderError("Structured REST request failed (HTTP 403)")

    def crawl_page(self, url: str) -> CrawlResult:
        self.crawl_calls += 1
        raise ProviderError("Structured REST request failed (HTTP 403)")


def test_auto_mode_falls_back_and_remembers_mcp_failure() -> None:
    mcp = FakeMCP(fail=True)
    rest = FakeRest()
    router = SearchRouter(mcp, rest, mode="auto")  # type: ignore[arg-type]

    first = asyncio.run(router.search_web("first"))
    second = asyncio.run(router.search_web("second"))

    assert first.transport == "rest"
    assert first.fallback_reason == "MCP unavailable"
    assert second.transport == "rest"
    assert mcp.search_calls == 1
    assert rest.search_calls == 2
    assert router.mcp_healthy is False


def test_auto_mode_keeps_mcp_when_healthy() -> None:
    mcp = FakeMCP(fail=False)
    rest = FakeRest()
    router = SearchRouter(mcp, rest, mode="auto")  # type: ignore[arg-type]

    result = asyncio.run(router.search_web("query"))

    assert result.transport == "mcp"
    assert mcp.search_calls == 1
    assert rest.search_calls == 0
    assert router.mcp_healthy is True


def test_rest_mode_never_calls_mcp() -> None:
    mcp = FakeMCP(fail=False)
    rest = FakeRest()
    router = SearchRouter(mcp, rest, mode="rest")  # type: ignore[arg-type]

    result = asyncio.run(router.crawl_page("https://example.com"))

    assert result.transport == "rest"
    assert mcp.crawl_calls == 0
    assert rest.crawl_calls == 1


def test_rest_authorization_failure_falls_back_to_public_web() -> None:
    mcp = FakeMCP(fail=False)
    rest = FailingRest()
    public = FakePublic()
    router = SearchRouter(  # type: ignore[arg-type]
        mcp,
        rest,
        mode="rest",
        public=public,
    )

    search = asyncio.run(router.search_web("query"))
    crawl = asyncio.run(router.crawl_page("https://example.com"))

    assert search.transport == "public"
    assert crawl.transport == "public"
    assert "HTTP 403" in (search.fallback_reason or "")
    assert public.search_calls == 1
    assert public.crawl_calls == 1
