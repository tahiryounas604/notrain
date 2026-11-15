"""robots.txt parsing following RFC 9309 semantics.

Implemented subset (the parts that decide access):

- Groups: one or more ``User-agent`` lines followed by ``Allow`` /
  ``Disallow`` rules. Field names are case-insensitive, product
  tokens are matched case-insensitively.
- Comments (``#`` to end of line) and blank lines are ignored.
- Group selection: all groups naming the queried agent are merged.
  If no group names the agent, the ``*`` groups are merged and used.
  Specific groups take precedence over ``*`` groups.
- Rule matching: patterns are matched from the start of the path,
  ``*`` matches any sequence of characters, a trailing ``$``
  anchors the pattern to the end of the path.
- Rule selection: among matching rules the longest pattern wins;
  on a tie ``Allow`` wins over ``Disallow`` (least restrictive,
  per RFC 9309 section 2.2.2). No matching rule means allowed.
- Empty ``Disallow:`` means "no restriction" and is ignored, as is
  an empty ``Allow:``.

``Sitemap:`` lines are collected. ``Crawl-delay:`` is not part of
RFC 9309 and is ignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Rule:
    kind: str  # "allow" or "disallow"
    pattern: str

    def matches(self, path: str) -> bool:
        return _pattern_matches(self.pattern, path)


@dataclass
class Group:
    agents: list[str] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)


@dataclass
class RobotsTxt:
    groups: list[Group] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    raw: str = ""

    # -- group selection -------------------------------------------------
    def groups_for(self, agent: str) -> list[Group]:
        """Merged groups applicable to *agent* (specific, else ``*``)."""
        low = agent.lower()
        specific = [g for g in self.groups
                    if any(a.lower() == low for a in g.agents)]
        if specific:
            return specific
        return [g for g in self.groups if "*" in g.agents]

    def rules_for(self, agent: str) -> list[Rule]:
        rules: list[Rule] = []
        for g in self.groups_for(agent):
            rules.extend(g.rules)
        return rules

    # -- access decision ---------------------------------------------------
    def deciding_rule(self, agent: str, path: str) -> Rule | None:
        """The rule that decides access to *path* for *agent*, or None."""
        if not path.startswith("/"):
            path = "/" + path
        best: Rule | None = None
        for rule in self.rules_for(agent):
            if not rule.pattern:
                continue
            if not rule.matches(path):
                continue
            if best is None or len(rule.pattern) > len(best.pattern):
                best = rule
            elif (len(rule.pattern) == len(best.pattern)
                  and rule.kind == "allow" and best.kind == "disallow"):
                best = rule  # tie: least restrictive wins
        return best

    def is_allowed(self, agent: str, path: str = "/") -> bool:
        rule = self.deciding_rule(agent, path)
        return rule is None or rule.kind == "allow"


def _pattern_matches(pattern: str, path: str) -> bool:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    regex = "^" + ".*".join(re.escape(part) for part in body.split("*"))
    if anchored:
        regex += "$"
    return re.match(regex, path) is not None


def parse_robots(text: str) -> RobotsTxt:
    robots = RobotsTxt(raw=text)
    current: Group | None = None
    current_has_rules = False

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            continue
        name, _, value = line.partition(":")
        name = name.strip().lower()
        value = value.strip()

        if name == "user-agent":
            if current is None or current_has_rules:
                current = Group()
                robots.groups.append(current)
                current_has_rules = False
            current.agents.append(value)
        elif name in ("allow", "disallow"):
            if current is None:
                # Rule outside any group: ignore (invalid per RFC 9309).
                continue
            current_has_rules = True
            if value == "":
                continue  # empty rule = no restriction
            current.rules.append(Rule(kind=name, pattern=value))
        elif name == "sitemap":
            robots.sitemaps.append(value)
        else:
            # Unknown / extension fields (crawl-delay, host, ...): if a
            # group already has rules, a following user-agent starts a
            # new group; unknown fields themselves are ignored.
            continue
    return robots
