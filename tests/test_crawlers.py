from notrain.crawlers import (CLASSIFICATIONS, CRAWLERS, by_classification,
                              get_crawler)


def test_db_size_about_twenty():
    assert 20 <= len(CRAWLERS) <= 30


def test_each_entry_has_token_and_valid_classification():
    for c in CRAWLERS:
        assert c.token and " " not in c.token
        assert c.classification in CLASSIFICATIONS
        assert c.operator


def test_tokens_unique_case_insensitive():
    tokens = [c.token.lower() for c in CRAWLERS]
    assert len(tokens) == len(set(tokens))


def test_well_known_tokens_present_with_expected_class():
    expected = {
        "GPTBot": "training",
        "OAI-SearchBot": "search",
        "ChatGPT-User": "user-fetch",
        "ClaudeBot": "training",
        "PerplexityBot": "search",
        "Perplexity-User": "user-fetch",
        "Google-Extended": "training",
        "Applebot-Extended": "training",
        "CCBot": "training",
        "Bytespider": "training",
        "Meta-ExternalAgent": "training",
        "Amazonbot": "search",
        "cohere-ai": "training",
        "MistralAI-User": "user-fetch",
    }
    for token, classification in expected.items():
        c = get_crawler(token)
        assert c is not None, token
        assert c.classification == classification, token


def test_all_classifications_represented():
    for classification in CLASSIFICATIONS:
        assert by_classification(classification), classification
