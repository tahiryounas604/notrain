from notrain.parser import parse_robots


def test_groups_and_agents():
    r = parse_robots("User-agent: GPTBot\nDisallow: /\n\n"
                     "User-agent: *\nDisallow: /tmp/\n")
    assert len(r.groups) == 2
    assert r.groups[0].agents == ["GPTBot"]
    assert not r.is_allowed("GPTBot", "/anything")
    assert r.is_allowed("OtherBot", "/anything")
    assert not r.is_allowed("OtherBot", "/tmp/x")


def test_multiple_agents_one_group():
    r = parse_robots("User-agent: GPTBot\nUser-agent: CCBot\nDisallow: /\n")
    assert len(r.groups) == 1
    assert not r.is_allowed("GPTBot", "/")
    assert not r.is_allowed("CCBot", "/")


def test_comments_and_blank_lines_ignored():
    r = parse_robots("# comment\n\nUser-agent: GPTBot # inline\n"
                     "Disallow: / # trailing\n\n# end\n")
    assert not r.is_allowed("GPTBot", "/x")
    assert r.groups[0].agents == ["GPTBot"]


def test_case_insensitive_fields_and_tokens():
    r = parse_robots("user-agent: gptbot\nDISALLOW: /\n")
    assert not r.is_allowed("GPTBot", "/")
    assert not r.is_allowed("GPTBOT", "/")


def test_group_merging_for_same_agent():
    # Two separate groups for the same agent must both apply.
    r = parse_robots("User-agent: GPTBot\nDisallow: /a/\n\n"
                     "User-agent: GPTBot\nDisallow: /b/\n")
    assert not r.is_allowed("GPTBot", "/a/1")
    assert not r.is_allowed("GPTBot", "/b/1")
    assert r.is_allowed("GPTBot", "/c/1")


def test_specific_group_beats_star_group():
    r = parse_robots("User-agent: *\nDisallow: /\n\n"
                     "User-agent: GPTBot\nAllow: /\n")
    assert r.is_allowed("GPTBot", "/x")
    assert not r.is_allowed("OtherBot", "/x")


def test_wildcard_star():
    r = parse_robots("User-agent: *\nDisallow: /*.pdf\n")
    assert not r.is_allowed("AnyBot", "/docs/file.pdf")
    assert r.is_allowed("AnyBot", "/docs/file.html")


def test_dollar_anchor():
    r = parse_robots("User-agent: *\nDisallow: /page$\n")
    assert not r.is_allowed("AnyBot", "/page")
    assert r.is_allowed("AnyBot", "/page/extra")
    assert r.is_allowed("AnyBot", "/pages")


def test_longest_match_wins():
    r = parse_robots("User-agent: *\nDisallow: /private/\n"
                     "Allow: /private/public/\n")
    assert not r.is_allowed("AnyBot", "/private/secret")
    assert r.is_allowed("AnyBot", "/private/public/page")


def test_tie_allow_wins():
    r = parse_robots("User-agent: *\nDisallow: /same\nAllow: /same\n")
    assert r.is_allowed("AnyBot", "/same")


def test_empty_disallow_means_allow_all():
    r = parse_robots("User-agent: *\nDisallow:\n")
    assert r.is_allowed("AnyBot", "/anything")


def test_no_matching_rule_allowed_by_default():
    r = parse_robots("")
    assert r.is_allowed("GPTBot", "/")
    assert r.deciding_rule("GPTBot", "/") is None


def test_deciding_rule_reported():
    r = parse_robots("User-agent: GPTBot\nDisallow: /train/\n")
    rule = r.deciding_rule("GPTBot", "/train/data")
    assert rule is not None and rule.kind == "disallow"
    assert rule.pattern == "/train/"


def test_sitemaps_collected():
    r = parse_robots("Sitemap: https://example.com/sitemap.xml\n"
                     "User-agent: *\nAllow: /\n")
    assert r.sitemaps == ["https://example.com/sitemap.xml"]


def test_new_group_after_rules():
    r = parse_robots("User-agent: A\nDisallow: /a\n"
                     "User-agent: B\nDisallow: /b\n")
    assert len(r.groups) == 2
    assert r.groups[1].agents == ["B"]
