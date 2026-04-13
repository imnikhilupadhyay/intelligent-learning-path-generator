"""Text normalization and simple keyword helpers."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable


def strip_html_tags(text: str) -> str:
    """Remove HTML tags and normalize a few common entities.

    Args:
        text: Raw text that may contain HTML markup.

    Returns:
        Plain-text approximation with tags removed.
    """
    if not isinstance(text, str):
        return ""
    # Break lines at <br> before stripping all tags.
    s = re.sub(r"(?i)<br\s*/?>", " ", text)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    return normalize_whitespace(s)


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and strip ends.

    Args:
        text: Input string.

    Returns:
        Normalized string.
    """
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text).strip()


def lowercase_copy(text: str) -> str:
    """Return a lowercased copy for keyword matching.

    Args:
        text: Input string.

    Returns:
        Lowercased string or empty if not a string.
    """
    if not isinstance(text, str):
        return ""
    return text.lower()


def fold_unicode(text: str) -> str:
    """ASCII-fold unicode for fuzzy comparisons.

    Args:
        text: Input string.

    Returns:
        ASCII-like folded string.
    """
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def count_keyword_hits(haystack: str, keywords: Iterable[str]) -> int:
    """Count how many distinct keywords appear in haystack (substring match).

    Args:
        haystack: Text to search (should be lowercased by caller if needed).
        keywords: Keywords to look for.

    Returns:
        Number of keywords with at least one hit.
    """
    if not haystack:
        return 0
    h = haystack.lower()
    hits = 0
    for kw in keywords:
        if not kw:
            continue
        if str(kw).lower() in h:
            hits += 1
    return hits
