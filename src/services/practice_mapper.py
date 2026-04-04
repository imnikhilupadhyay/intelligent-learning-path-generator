"""Practice → skill keyword mapping from YAML config."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from utils.constants import COL_EMP_PRACTISE, PRACTICE_MAP_YAML
from utils.file_utils import load_yaml_cached
from utils.text_utils import normalize_whitespace


_PRACTICE_ALIASES: dict[str, str] = {
    "application service": "Application Services",
    "application services": "Application Services",
    "appservices": "Application Services",
    "bps": "BPS",
    "business process services": "BPS",
    "cloud and security": "Cloud & Security",
    "cloud & security": "Cloud & Security",
    "cloud security": "Cloud & Security",
    "global support": "Global Support",
}


def normalize_practice(practice_raw: str | None) -> str | None:
    """Normalize practice label for config lookup.

    Args:
        practice_raw: Value from user master ``emp_practise``.

    Returns:
        Canonical practice key or ``None``.
    """
    if practice_raw is None:
        return None
    s = normalize_whitespace(str(practice_raw))
    if not s:
        return None
    key = s.strip()
    alias = _PRACTICE_ALIASES.get(key.lower())
    if alias:
        return alias
    # Title case heuristic for minor variations
    for canon, alias_val in _PRACTICE_ALIASES.items():
        if alias_val.lower() == key.lower():
            return alias_val
    return key


def skills_for_practice(practice_raw: str | None) -> list[str]:
    """Return skill keywords for a practice from config.

    Args:
        practice_raw: Raw ``emp_practise`` value.

    Returns:
        List of skill keywords (may be empty).
    """
    cfg: Mapping[str, Any] = load_yaml_cached(PRACTICE_MAP_YAML)
    practice = normalize_practice(practice_raw)
    if practice is None:
        return []
    entry = cfg.get(practice)
    if isinstance(entry, Mapping):
        skills = entry.get("skills") or []
        return [str(s) for s in skills if s]
    return []


def build_retrieval_query_phrase(
    practice_raw: str | None,
    target_expertise: str | None,
    extra: Sequence[str] | None = None,
) -> str:
    """Compose a single retrieval query string.

    Args:
        practice_raw: Employee practice.
        target_expertise: Optional focus area.
        extra: Optional extra tokens.

    Returns:
        Space-separated query words.
    """
    parts: list[str] = []
    p = normalize_practice(practice_raw)
    if p:
        parts.append(p)
    parts.extend(skills_for_practice(practice_raw))
    if target_expertise:
        parts.append(str(target_expertise))
    if extra:
        parts.extend(str(x) for x in extra)
    return normalize_whitespace(" ".join(parts))
