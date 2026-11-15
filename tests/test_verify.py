from notrain.crawlers import get_crawler
from notrain.fetch import (fetch_robots_text, load_robots, verify_crawler,
                           verify_site)
from notrain.parser import parse_robots


def _by_token(results):
    return {r.token: r for r in results}


def test_fetch_robots_from_local_server(local_server):
    text = fetch_robots_text(local_server)
    assert "GPTBot" in text


def test_load_robots_from_url(local_server):
    robots = load_robots(local_server)
    assert not robots.is_allowed("GPTBot", "/")


def test_verify_agreement_blocked_both(local_server):
    results = _by_token(verify_site(local_server))
    gpt = results["GPTBot"]
    assert gpt.robots_allowed is False
    assert gpt.http_status == 403
    assert gpt.server_allowed is False
    assert gpt.agrees is True


def test_verify_agreement_allowed_both(local_server):
    results = _by_token(verify_site(local_server))
    perplexity = results["PerplexityBot"]
    assert perplexity.robots_allowed is True
    assert perplexity.http_status == 200
    assert perplexity.agrees is True


def test_verify_mismatch_server_blocks_what_robots_allows(local_server):
    results = _by_token(verify_site(local_server))
    byte = results["Bytespider"]
    assert byte.robots_allowed is True
    assert byte.http_status == 403
    assert byte.agrees is False


def test_verify_mismatch_on_private_path(local_server):
    robots = parse_robots(fetch_robots_text(local_server))
    result = verify_crawler(local_server, get_crawler("CCBot"),
                            robots, path="/private/")
    assert result.robots_allowed is False   # robots.txt blocks /private/
    assert result.http_status == 200        # ...but the server serves it
    assert result.agrees is False
