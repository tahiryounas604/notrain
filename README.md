# notrain

AI crawler control + monitoring for websites. `notrain` tells you what
your `robots.txt` actually says about the AI crawlers that matter —
GPTBot, ClaudeBot, PerplexityBot, CCBot and ~18 more — generates a
correct `robots.txt` from a simple policy, verifies the policy against
your server's live HTTP behaviour, and monitors sites for changes.

Pure Python, standard library only. No third-party dependencies.

## Features

- **RFC 9309 robots.txt parser** — user-agent groups, `Allow` /
  `Disallow`, wildcards (`*` and `$`), group merging for a given agent,
  specific-group-over-`*` selection, and longest-match rule selection
  (ties go to `Allow`, the least restrictive rule).
- **Bundled crawler database** — 22 real AI crawlers, each with its
  real user-agent token, operator, and a functional classification:
  `training`, `search`, or `user-fetch` (e.g. GPTBot = training,
  OAI-SearchBot = search, ChatGPT-User = user-fetch, ClaudeBot,
  Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User,
  Google-Extended, Applebot, Applebot-Extended, CCBot, Bytespider,
  Meta-ExternalAgent, Meta-ExternalFetcher, Amazonbot, cohere-ai,
  MistralAI-User, YouBot, Diffbot, DuckAssistBot, anthropic-ai).
- **Verdict engine** — per crawler: allowed or blocked for a given
  path, plus the exact rule that decided it.
- **Generator** — turn a policy ("block training, allow search") into
  a correct `robots.txt`. Round-trip guaranteed by the test suite:
  parsing the generated file reproduces the intended verdict for
  every crawler in the database.
- **Active verification** — fetch a page once per crawler user-agent
  and compare the server's actual response (200 vs 403/401) against
  what `robots.txt` claims; mismatches are flagged.
- **Monitor mode** — snapshot a site's verdicts (JSON store, with the
  robots.txt SHA-256 hash); on re-run, diff against the previous
  snapshot and report which crawlers' status changed.

## Install

Python 3.11 or 3.12. Standard library only.

```bash
git clone https://github.com/tahiryounas604/notrain.git
cd notrain
pip install .
# or run without installing:
python3 notrain.py --help
```

## Usage

```bash
# What does a site's (or a local file's) robots.txt say about AI crawlers?
notrain check https://example.com
notrain check ./robots.txt --path /private/
notrain check https://example.com --json

# Generate a robots.txt from a policy
notrain generate --block training --allow search
notrain generate --block training --block user-fetch -o robots.txt

# Does the server actually behave the way robots.txt claims?
notrain verify https://example.com
notrain verify https://example.com --path /private/

# Snapshot now, diff on the next run
notrain monitor https://example.com --store .notrain-snapshots
notrain monitor https://example.com --store .notrain-snapshots   # again -> change report
```

Example `check` output (against `examples/sample-robots.txt`):

```
GPTBot                   training    blocked  Disallow: /
CCBot                    training    blocked  Disallow: /
PerplexityBot            search      allowed  Allow: /
```

Example generated `robots.txt` (`generate --block training --allow search`):
one explicit group per crawler — blocked crawlers get `Disallow: /`,
allowed crawlers get `Allow: /` — followed by a permissive `*` group.

## Architecture

```
src/notrain/
├── crawlers.py   # the crawler database (token, operator, classification)
├── parser.py     # RFC 9309 parser + rule matching / group selection
├── verdict.py    # per-crawler verdicts + deciding rule
├── generator.py  # policy -> robots.txt (round-trip safe)
├── fetch.py      # robots.txt fetching + active verification
├── monitor.py    # JSON snapshots + diffing
└── cli.py        # argparse CLI: check / generate / verify / monitor
notrain.py        # no-install entry point (adds src/ to sys.path)
tests/            # pytest suite; verification tests use a local
                  # http.server fixture -- no live internet
```

Data flow: `parser` turns text into groups/rules → `verdict` applies
them per crawler → `check`, `verify` and `monitor` are three views of
the same verdicts (stated policy, live behaviour, change over time).
`generator` runs the flow in reverse, from policy to text.

## Tests

```bash
python3 -m pytest -q
```

The suite covers: parser groups / wildcards / `$` anchor /
longest-match / tie-breaking / group merging / comments; the
generator round-trip property for several policies; snapshot diff
logic (changed / unchanged / first run); crawler-database integrity;
the CLI; and active verification against a local test HTTP server
that serves a fixture `robots.txt` and 403s specific user-agents.
Tests never hit the live internet.

## Honest limits

- **robots.txt is advisory.** Verdicts describe a site's *stated*
  policy. Well-behaved crawlers honour it; others may not, and a
  `Disallow` is not access control. If you must keep a crawler out,
  enforce it server-side (user-agent / IP rules, authentication) —
  `verify` only samples that enforcement.
- **Active verification samples only the tested paths.** A 200/403
  result for `/` says nothing about `/private/` or any other path,
  and a single request per crawler cannot detect rate-based or
  IP-based blocking, JavaScript challenges, or CAPTCHAs. Statuses
  other than 200/3xx/401/403 are reported as inconclusive.
- **Not all crawlers honour robots.txt**, and some fetch with
  user-agent strings that differ from their robots.txt token or
  rotate over time. The database reflects operators' published
  tokens and stated purposes at the time of writing; operators
  change both.
- **Classifications are functional, not legal.** "Training" means
  the operator describes the crawl as feeding model training; it
  is not a judgement about any crawler's data practices.
- **Parser scope:** the access-deciding parts of RFC 9309 are
  implemented; `Crawl-delay` (not in RFC 9309) is ignored, percent-
  encoding edge cases are compared literally, and `Sitemap:` lines
  are collected but not validated.
- **Monitor snapshots are local JSON files** — no scheduling,
  alerting, or dashboard. Run it from cron if you want periodic
  checks.

## License

GPL-3.0 — see [LICENSE](LICENSE).

## Author

Tahir Younas — Tytechlabs — https://www.linkedin.com/in/tahiryounas604
