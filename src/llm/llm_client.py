"""Thin optional OpenAI-compatible client."""

from __future__ import annotations

import os
from typing import Any

from utils.logging_utils import get_logger

logger = get_logger(__name__)


class LlmClient:
    """Best-effort OpenAI chat completion wrapper."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize client from arguments or environment."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get(
            "AZURE_OPENAI_API_KEY",
            "",
        )
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def is_configured(self) -> bool:
        """Return True if an API key is present."""
        return bool(self.api_key and self.api_key.strip())

    def complete(self, user_prompt: str, system: str | None = None) -> str:
        """Run a chat completion (OpenAI-compatible REST).

        Args:
            user_prompt: User message content.
            system: Optional system prompt.

        Returns:
            Assistant text.

        Raises:
            RuntimeError: On HTTP or API errors.
        """
        try:
            import requests
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("requests package required for LLM client") from exc

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_prompt})
        payload = {"model": self.model, "messages": messages, "temperature": 0.2}
        url = self.base_url.rstrip("/") + "/chat/completions"
        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        if resp.status_code >= 400:
            logger.error("LLM HTTP %s: %s", resp.status_code, resp.text[:500])
            resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response missing choices")
        content = choices[0].get("message", {}).get("content", "")
        return str(content)
