"""Optional LLM-based metadata extraction with JSON enforcement."""

from __future__ import annotations

import json
from typing import Any, Mapping

from llm.llm_client import LlmClient
from llm.prompts import build_metadata_extraction_prompt
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def extract_metadata_with_llm(summary: str, client: LlmClient | None = None) -> Mapping[str, Any] | None:
    """Ask the LLM for structured metadata; return None on failure.

    Args:
        summary: Raw course summary text.
        client: Optional :class:`LlmClient`.

    Returns:
        Parsed JSON mapping or ``None`` if unavailable or invalid.
    """
    c = client or LlmClient()
    if not c.is_configured() or not summary:
        return None
    prompt = build_metadata_extraction_prompt(summary)
    try:
        raw = c.complete(
            prompt,
            system="You return only valid JSON objects. No markdown fences.",
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.split("\n", 1)[-1] if "\n" in raw else raw
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.debug("LLM metadata extraction failed: %s", exc)
        return None
