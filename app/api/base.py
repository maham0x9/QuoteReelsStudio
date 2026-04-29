"""Shared keyword extraction + base provider interface."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.models import BackgroundOption

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "of", "in", "on", "at", "to",
    "for", "with", "is", "are", "was", "were", "be", "being", "been", "as", "by",
    "this", "that", "these", "those", "it", "its", "i", "you", "he", "she", "we",
    "they", "them", "your", "my", "our", "their", "us", "me", "do", "does", "did",
    "not", "no", "yes", "so", "than", "too", "very", "can", "will", "just", "from",
    "about", "into", "over", "under", "out", "up", "down", "more", "most", "some",
    "any", "all", "every", "each", "one", "two", "three", "what", "when", "where",
    "why", "how", "who", "have", "has", "had", "make", "makes", "made", "get", "got",
    "go", "goes", "going", "there", "here",
}


def extract_keywords(text: str, max_words: int = 4) -> str:
    """Pull a short search phrase out of a quote.

    The result is a space-separated string of distinct, non-stopword tokens
    (preserving order of first appearance). Falls back to ``"motivation nature"``
    when the quote is empty or has no usable tokens.
    """
    if not text:
        return "motivation nature"
    words = re.findall(r"[A-Za-z']+", text.lower())
    seen: list[str] = []
    for w in words:
        if w in _STOPWORDS or len(w) < 3:
            continue
        if w in seen:
            continue
        seen.append(w)
        if len(seen) >= max_words:
            break
    if not seen:
        return "motivation nature"
    return " ".join(seen)


class BackgroundProvider(ABC):
    name: str = "base"

    @abstractmethod
    def search(self, query: str, per_page: int = 10) -> list[BackgroundOption]:
        ...

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        ...
