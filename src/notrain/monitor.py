"""Monitor mode: snapshot a site's verdicts, diff on re-run.

Snapshots are JSON files, one per site, in a store directory.
A snapshot records the robots.txt SHA-256 hash and the per-crawler
verdict for the checked path. Re-running produces a diff: which
crawlers changed status, and whether robots.txt itself changed.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .parser import RobotsTxt
from .verdict import all_verdicts


def make_snapshot(source: str, robots: RobotsTxt,
                  path: str = "/") -> dict:
    verdicts = {}
    for v in all_verdicts(robots, path):
        verdicts[v.token] = {
            "classification": v.classification,
            "allowed": v.allowed,
            "matched_rule": v.matched_rule,
        }
    return {
        "source": source,
        "path": path,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "robots_sha256": hashlib.sha256(
            robots.raw.encode("utf-8")).hexdigest(),
        "verdicts": verdicts,
    }


@dataclass
class SnapshotDiff:
    is_first_run: bool
    robots_hash_changed: bool
    changed: list[dict] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changed) or self.robots_hash_changed


def diff_snapshots(old: dict | None, new: dict) -> SnapshotDiff:
    if old is None:
        return SnapshotDiff(is_first_run=True, robots_hash_changed=False,
                            unchanged=sorted(new["verdicts"]))
    changed: list[dict] = []
    unchanged: list[str] = []
    old_v = old.get("verdicts", {})
    for token, new_entry in sorted(new["verdicts"].items()):
        old_entry = old_v.get(token)
        if old_entry is None:
            changed.append({"token": token, "before": None,
                            "after": new_entry["allowed"]})
        elif old_entry.get("allowed") != new_entry["allowed"]:
            changed.append({"token": token,
                            "before": old_entry.get("allowed"),
                            "after": new_entry["allowed"]})
        else:
            unchanged.append(token)
    return SnapshotDiff(
        is_first_run=False,
        robots_hash_changed=old.get("robots_sha256") != new["robots_sha256"],
        changed=changed, unchanged=unchanged)


def snapshot_filename(source: str) -> str:
    parsed = urlparse(source)
    base = parsed.netloc or parsed.path or source
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("_") or "site"
    return f"{slug}.json"


def load_snapshot(store_dir: str | Path, source: str) -> dict | None:
    path = Path(store_dir) / snapshot_filename(source)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_snapshot(store_dir: str | Path, snapshot: dict) -> Path:
    store = Path(store_dir)
    store.mkdir(parents=True, exist_ok=True)
    path = store / snapshot_filename(snapshot["source"])
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def monitor_run(source: str, robots: RobotsTxt, store_dir: str | Path,
                path: str = "/") -> tuple[dict, SnapshotDiff]:
    """Snapshot *robots* for *source*, diff vs stored, store the new one."""
    previous = load_snapshot(store_dir, source)
    snapshot = make_snapshot(source, robots, path)
    diff = diff_snapshots(previous, snapshot)
    save_snapshot(store_dir, snapshot)
    return snapshot, diff
