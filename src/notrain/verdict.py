"""Verdict engine: what a robots.txt says about each known crawler."""
from __future__ import annotations

from dataclasses import dataclass

from .crawlers import CRAWLERS, Crawler
from .parser import RobotsTxt


@dataclass(frozen=True)
class Verdict:
    crawler: Crawler
    allowed: bool
    path: str
    matched_rule: str | None  # e.g. "Disallow: /private/"
    rule_kind: str | None     # "allow" / "disallow" / None

    @property
    def token(self) -> str:
        return self.crawler.token

    @property
    def classification(self) -> str:
        return self.crawler.classification

    @property
    def status(self) -> str:
        return "allowed" if self.allowed else "blocked"


def verdict_for(robots: RobotsTxt, crawler: Crawler,
                path: str = "/") -> Verdict:
    rule = robots.deciding_rule(crawler.token, path)
    allowed = rule is None or rule.kind == "allow"
    matched = None
    if rule is not None:
        matched = f"{rule.kind.capitalize()}: {rule.pattern}"
    return Verdict(crawler=crawler, allowed=allowed, path=path,
                   matched_rule=matched,
                   rule_kind=rule.kind if rule else None)


def all_verdicts(robots: RobotsTxt, path: str = "/",
                 crawlers=CRAWLERS) -> list[Verdict]:
    return [verdict_for(robots, c, path) for c in crawlers]
