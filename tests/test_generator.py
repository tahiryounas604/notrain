import pytest

from notrain.crawlers import CLASSIFICATIONS, CRAWLERS
from notrain.generator import generate_robots, policy_from_lists
from notrain.parser import parse_robots
from notrain.verdict import all_verdicts


def _round_trip(policy):
    text = generate_robots(policy)
    robots = parse_robots(text)
    verdicts = {v.token: v.allowed for v in all_verdicts(robots)}
    for crawler in CRAWLERS:
        intended = policy.get(crawler.classification, True)
        assert verdicts[crawler.token] == intended, (
            crawler.token, crawler.classification, policy)
    return text


def test_round_trip_block_training_only():
    _round_trip({"training": False})


def test_round_trip_block_training_and_user_fetch():
    _round_trip({"training": False, "user-fetch": False,
                 "search": True})


def test_round_trip_allow_everything():
    _round_trip({})


def test_round_trip_block_everything():
    _round_trip({c: False for c in CLASSIFICATIONS})


def test_round_trip_block_search_only():
    _round_trip({"search": False, "training": True})


def test_policy_from_lists():
    policy = policy_from_lists(block=["training"], allow=["search"])
    assert policy == {"training": False, "search": True}


def test_policy_conflict_rejected():
    with pytest.raises(ValueError):
        policy_from_lists(block=["training"], allow=["training"])


def test_unknown_classification_rejected():
    with pytest.raises(ValueError):
        generate_robots({"bogus": False})
    with pytest.raises(ValueError):
        policy_from_lists(block=["bogus"])


def test_generated_text_names_every_crawler():
    text = generate_robots({"training": False})
    for crawler in CRAWLERS:
        assert f"User-agent: {crawler.token}" in text
