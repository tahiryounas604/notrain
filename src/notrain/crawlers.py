"""Bundled database of well-known AI crawlers.

Tokens are the product tokens the crawlers declare in their
User-Agent strings and that site operators use in robots.txt.
Classifications are functional, based on the operator's own
published description of what the crawler does:

- ``training``   -- crawls content to train / improve models.
- ``search``     -- crawls to build a search / answer index.
- ``user-fetch`` -- fetches a page on behalf of a live user request
  (e.g. a chat user pasting or following a link).

Classifications describe the operator's stated purpose at the time
of writing; operators can and do change what a token is used for,
so treat the classification as guidance, not a guarantee.
"""
from __future__ import annotations

from dataclasses import dataclass

CLASSIFICATIONS = ("training", "search", "user-fetch")


@dataclass(frozen=True)
class Crawler:
    token: str
    classification: str
    operator: str
    description: str = ""

    def __post_init__(self) -> None:
        if self.classification not in CLASSIFICATIONS:
            raise ValueError(f"unknown classification: {self.classification!r}")


CRAWLERS: tuple[Crawler, ...] = (
    Crawler("GPTBot", "training", "OpenAI",
            "Crawls content that may be used to train OpenAI models."),
    Crawler("OAI-SearchBot", "search", "OpenAI",
            "Search crawler for ChatGPT search results."),
    Crawler("ChatGPT-User", "user-fetch", "OpenAI",
            "Fetches pages on behalf of a ChatGPT user."),
    Crawler("ClaudeBot", "training", "Anthropic",
            "Anthropic crawler used to improve and train models."),
    Crawler("Claude-SearchBot", "search", "Anthropic",
            "Search / retrieval crawler for Claude features."),
    Crawler("Claude-User", "user-fetch", "Anthropic",
            "Fetches pages on behalf of a Claude user."),
    Crawler("anthropic-ai", "training", "Anthropic",
            "Legacy Anthropic crawler token."),
    Crawler("PerplexityBot", "search", "Perplexity",
            "Indexes pages for Perplexity search results."),
    Crawler("Perplexity-User", "user-fetch", "Perplexity",
            "Fetches pages on behalf of a Perplexity user."),
    Crawler("Google-Extended", "training", "Google",
            "Controls whether crawled content is used to train "
            "Google AI models; does not affect Google Search ranking."),
    Crawler("Applebot", "search", "Apple",
            "Apple's web crawler for search and Siri results."),
    Crawler("Applebot-Extended", "training", "Apple",
            "Controls use of Applebot-crawled content for training "
            "Apple AI models."),
    Crawler("CCBot", "training", "Common Crawl",
            "Common Crawl crawler; its corpus is widely used for "
            "model training."),
    Crawler("Bytespider", "training", "ByteDance",
            "ByteDance crawler reported to collect training data."),
    Crawler("Meta-ExternalAgent", "training", "Meta",
            "Meta crawler used to train AI models."),
    Crawler("Meta-ExternalFetcher", "user-fetch", "Meta",
            "Fetches pages on behalf of users of Meta AI products."),
    Crawler("Amazonbot", "search", "Amazon",
            "Amazon crawler for Alexa / Amazon search features."),
    Crawler("cohere-ai", "training", "Cohere",
            "Cohere crawler token used for model-related crawling."),
    Crawler("MistralAI-User", "user-fetch", "Mistral AI",
            "Fetches pages on behalf of a Mistral AI user."),
    Crawler("YouBot", "search", "You.com",
            "You.com search crawler."),
    Crawler("Diffbot", "training", "Diffbot",
            "Diffbot extraction crawler; extracted corpora are "
            "used in AI datasets."),
    Crawler("DuckAssistBot", "user-fetch", "DuckDuckGo",
            "Fetches pages to answer a DuckDuckGo AI chat query."),
)


def get_crawler(token: str) -> Crawler | None:
    low = token.lower()
    for c in CRAWLERS:
        if c.token.lower() == low:
            return c
    return None


def by_classification(classification: str) -> list[Crawler]:
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"unknown classification: {classification!r}")
    return [c for c in CRAWLERS if c.classification == classification]
