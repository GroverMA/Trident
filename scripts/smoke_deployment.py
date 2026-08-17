"""Dependency-free smoke test for a deployed Trident region."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request


def request(url: str, *, expect_json: bool) -> None:
    with urllib.request.urlopen(url, timeout=20) as response:
        body = response.read()
        if response.status != 200:
            raise RuntimeError(f"{url}: HTTP {response.status}")
        if expect_json:
            payload = json.loads(body)
            if payload.get("status") not in {"ok", "ready"}:
                raise RuntimeError(f"{url}: unexpected payload {payload}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-url", required=True)
    parser.add_argument("--api-url", required=True)
    args = parser.parse_args()
    web = args.web_url.rstrip("/")
    api = args.api_url.rstrip("/")
    for url, expect_json in [
        (web, False),
        (f"{web}/healthz", True),
        (f"{api}/health", True),
        (f"{api}/ready", True),
    ]:
        request(url, expect_json=expect_json)
        print(f"PASS {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
