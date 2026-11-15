"""Fetching robots.txt and active verification.

Active verification samples reality: it requests a page once per
crawler user-agent and compares the HTTP status with what the
site's robots.txt claims. It samples only the paths it is asked
to test -- it does not prove how a server treats other paths.
"""
from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .crawlers import CRAWLERS, Crawler
from .parser import RobotsTxt, parse_robots
from .verdict import verdict_for

DEFAULT_TIMEOUT = 10.0
_BLOCKED_CODES = (401, 403)


def robots_url_for(url: str) -> str:
    if url.rstrip("/").endswith("/robots.txt"):
        return url
    return url.rstrip("/") + "/robots.txt"


def _http_get(url: str, user_agent: str,
              timeout: float = DEFAULT_TIMEOUT) -> tuple[int | None, str]:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return exc.code, body
    except (urllib.error.URLError, OSError, ValueError):
        return None, ""


def fetch_robots_text(url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Fetch the robots.txt for a site URL (or a direct robots.txt URL)."""
    status, body = _http_get(robots_url_for(url), "notrain/0.1", timeout)
    if status is None:
        raise ConnectionError(f"could not fetch robots.txt from {url}")
    if status == 404:
        return ""  # no robots.txt: everything is allowed by default
    return body


def load_robots(source: str, timeout: float = DEFAULT_TIMEOUT) -> RobotsTxt:
    """Load robots.txt from an http(s) URL or a local file path."""
    if source.startswith(("http://", "https://")):
        return parse_robots(fetch_robots_text(source, timeout))
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"no such file: {source}")
    return parse_robots(path.read_text(encoding="utf-8", errors="replace"))


def user_agent_for(crawler: Crawler) -> str:
    return f"Mozilla/5.0 (compatible; {crawler.token}/1.0; +notrain)"


@dataclass(frozen=True)
class VerifyResult:
    crawler: Crawler
    robots_allowed: bool
    http_status: int | None
    server_allowed: bool | None  # None = inconclusive status
    agrees: bool | None          # None = cannot judge

    @property
    def token(self) -> str:
        return self.crawler.token


def verify_crawler(base_url: str, crawler: Crawler, robots: RobotsTxt,
                   path: str = "/",
                   timeout: float = DEFAULT_TIMEOUT) -> VerifyResult:
    if not path.startswith("/"):
        path = "/" + path
    verdict = verdict_for(robots, crawler, path)
    url = base_url.rstrip("/") + path
    status, _ = _http_get(url, user_agent_for(crawler), timeout)
    if status is None:
        server_allowed = None
    elif status in _BLOCKED_CODES:
        server_allowed = False
    elif 200 <= status < 400:
        server_allowed = True
    else:
        server_allowed = None  # 404/5xx etc: no clear allow/block signal
    agrees = None
    if server_allowed is not None:
        agrees = server_allowed == verdict.allowed
    return VerifyResult(crawler=crawler, robots_allowed=verdict.allowed,
                        http_status=status, server_allowed=server_allowed,
                        agrees=agrees)


def verify_site(base_url: str, path: str = "/",
                timeout: float = DEFAULT_TIMEOUT,
                crawlers=CRAWLERS) -> list[VerifyResult]:
    robots = parse_robots(fetch_robots_text(base_url, timeout))
    return [verify_crawler(base_url, c, robots, path, timeout)
            for c in crawlers]
