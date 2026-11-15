from notrain.monitor import (diff_snapshots, load_snapshot, make_snapshot,
                             monitor_run)
from notrain.parser import parse_robots
from notrain.verdict import all_verdicts

ROBOTS_V1 = "User-agent: GPTBot\nDisallow: /\n"
ROBOTS_V2 = ("User-agent: GPTBot\nAllow: /\n\n"
             "User-agent: CCBot\nDisallow: /\n")


def test_verdict_engine_reports_deciding_rule():
    robots = parse_robots(ROBOTS_V1)
    verdicts = {v.token: v for v in all_verdicts(robots)}
    assert verdicts["GPTBot"].allowed is False
    assert verdicts["GPTBot"].matched_rule == "Disallow: /"
    # No group for CCBot and no * group: allowed, no rule.
    assert verdicts["CCBot"].allowed is True
    assert verdicts["CCBot"].matched_rule is None


def test_diff_detects_changed_and_unchanged():
    old = make_snapshot("https://example.com", parse_robots(ROBOTS_V1))
    new = make_snapshot("https://example.com", parse_robots(ROBOTS_V2))
    diff = diff_snapshots(old, new)
    assert not diff.is_first_run
    assert diff.robots_hash_changed
    changed = {c["token"]: c for c in diff.changed}
    assert changed["GPTBot"]["before"] is False
    assert changed["GPTBot"]["after"] is True
    assert changed["CCBot"]["before"] is True
    assert changed["CCBot"]["after"] is False
    assert "PerplexityBot" in diff.unchanged


def test_diff_no_changes():
    robots = parse_robots(ROBOTS_V1)
    old = make_snapshot("https://example.com", robots)
    new = make_snapshot("https://example.com", robots)
    diff = diff_snapshots(old, new)
    assert diff.changed == []
    assert not diff.robots_hash_changed
    assert not diff.has_changes


def test_diff_first_run():
    snap = make_snapshot("https://example.com", parse_robots(ROBOTS_V1))
    diff = diff_snapshots(None, snap)
    assert diff.is_first_run
    assert diff.changed == []


def test_monitor_run_stores_and_diffs(tmp_path):
    store = tmp_path / "snaps"
    _, diff1 = monitor_run("https://example.com",
                           parse_robots(ROBOTS_V1), store)
    assert diff1.is_first_run
    stored = load_snapshot(store, "https://example.com")
    assert stored is not None
    assert stored["verdicts"]["GPTBot"]["allowed"] is False

    _, diff2 = monitor_run("https://example.com",
                           parse_robots(ROBOTS_V2), store)
    assert not diff2.is_first_run
    assert {c["token"] for c in diff2.changed} == {"GPTBot", "CCBot"}
    stored2 = load_snapshot(store, "https://example.com")
    assert stored2["robots_sha256"] != stored["robots_sha256"]
