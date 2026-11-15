"""notrain command-line interface.

Usage:
    notrain check <url-or-file> [--path /] [--json]
    notrain generate [--block training] [--allow search] [--path /]
    notrain verify <url> [--path /] [--json]
    notrain monitor <url> [--store DIR] [--path /] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys

from .fetch import load_robots, verify_site
from .generator import generate_robots, policy_from_lists
from .monitor import monitor_run
from .verdict import all_verdicts


def _print_verdicts(verdicts) -> None:
    for v in verdicts:
        rule = v.matched_rule or "(no matching rule -- allowed by default)"
        print(f"{v.token:<24} {v.classification:<11} "
              f"{v.status:<8} {rule}")


def _cmd_check(args) -> int:
    try:
        robots = load_robots(args.source)
    except (FileNotFoundError, ConnectionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    verdicts = all_verdicts(robots, args.path)
    if args.json:
        print(json.dumps([{
            "token": v.token, "classification": v.classification,
            "allowed": v.allowed, "matched_rule": v.matched_rule,
        } for v in verdicts], indent=2))
    else:
        print(f"# {args.source}  path={args.path}")
        _print_verdicts(verdicts)
    return 0


def _cmd_generate(args) -> int:
    try:
        policy = policy_from_lists(block=args.block, allow=args.allow)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    text = generate_robots(policy, path=args.path)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(text, end="")
    return 0


def _cmd_verify(args) -> int:
    try:
        results = verify_site(args.url, path=args.path)
    except ConnectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps([{
            "token": r.token, "robots_allowed": r.robots_allowed,
            "http_status": r.http_status,
            "server_allowed": r.server_allowed, "agrees": r.agrees,
        } for r in results], indent=2))
    else:
        print(f"# verify {args.url}  path={args.path}")
        for r in results:
            if r.agrees is None:
                note = "inconclusive"
            elif r.agrees:
                note = "agrees"
            else:
                note = "MISMATCH"
            status = r.http_status if r.http_status is not None else "error"
            claim = "allowed" if r.robots_allowed else "blocked"
            print(f"{r.token:<24} robots={claim:<8} http={status!s:<6} {note}")
    return 0


def _cmd_monitor(args) -> int:
    try:
        robots = load_robots(args.url)
    except (FileNotFoundError, ConnectionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    snapshot, diff = monitor_run(args.url, robots, args.store,
                                 path=args.path)
    if args.json:
        print(json.dumps({
            "snapshot": snapshot,
            "diff": {
                "is_first_run": diff.is_first_run,
                "robots_hash_changed": diff.robots_hash_changed,
                "changed": diff.changed, "unchanged": diff.unchanged,
            },
        }, indent=2))
        return 0
    print(f"# monitor {args.url}  path={args.path}")
    print(f"robots.txt sha256: {snapshot['robots_sha256']}")
    if diff.is_first_run:
        print("first snapshot stored -- no previous snapshot to diff")
    else:
        print(f"robots.txt changed: {'yes' if diff.robots_hash_changed else 'no'}")
        if diff.changed:
            print("verdict changes:")
            for c in diff.changed:
                before = "allowed" if c["before"] else "blocked"
                if c["before"] is None:
                    before = "(new)"
                after = "allowed" if c["after"] else "blocked"
                print(f"  {c['token']}: {before} -> {after}")
        else:
            print("verdict changes: none")
        print(f"unchanged crawlers: {len(diff.unchanged)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="notrain",
        description="AI crawler control + monitoring: check what a "
                    "robots.txt says about AI crawlers, generate one "
                    "from a policy, verify it live, and monitor changes.")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="verdicts from a URL or local file")
    c.add_argument("source", help="site URL, robots.txt URL, or file path")
    c.add_argument("--path", default="/", help="path to test (default /)")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=_cmd_check)

    g = sub.add_parser("generate", help="generate robots.txt from a policy")
    g.add_argument("--block", action="append", default=[],
                   metavar="CLASS",
                   help="classification to block: training, search, "
                        "user-fetch (repeatable)")
    g.add_argument("--allow", action="append", default=[],
                   metavar="CLASS",
                   help="classification to explicitly allow (repeatable)")
    g.add_argument("--path", default="/", help="path the rules cover")
    g.add_argument("-o", "--output", help="write to file instead of stdout")
    g.set_defaults(func=_cmd_generate)

    v = sub.add_parser("verify", help="compare robots.txt claims with "
                                      "live HTTP responses per crawler")
    v.add_argument("url", help="site base URL")
    v.add_argument("--path", default="/")
    v.add_argument("--json", action="store_true")
    v.set_defaults(func=_cmd_verify)

    m = sub.add_parser("monitor", help="snapshot verdicts and diff "
                                       "against the previous snapshot")
    m.add_argument("url", help="site URL (or local robots.txt file)")
    m.add_argument("--store", default=".notrain-snapshots",
                   help="snapshot directory (default .notrain-snapshots)")
    m.add_argument("--path", default="/")
    m.add_argument("--json", action="store_true")
    m.set_defaults(func=_cmd_monitor)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
