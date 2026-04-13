"""Tests for LEARNING_PATH_TOP_K resolution."""

from __future__ import annotations

import pytest

from utils import constants


def test_get_retrieval_top_k_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset env uses default 15."""
    monkeypatch.delenv("LEARNING_PATH_TOP_K", raising=False)
    # Re-import would cache nothing; function reads os.environ each call
    assert constants.get_retrieval_top_k() == 15


def test_get_retrieval_top_k_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid or out-of-range values clamp or fall back."""
    monkeypatch.setenv("LEARNING_PATH_TOP_K", "40")
    assert constants.get_retrieval_top_k() == 40
    monkeypatch.setenv("LEARNING_PATH_TOP_K", "999")
    assert constants.get_retrieval_top_k() == 200
    monkeypatch.setenv("LEARNING_PATH_TOP_K", "0")
    assert constants.get_retrieval_top_k() == 1
    monkeypatch.setenv("LEARNING_PATH_TOP_K", "nope")
    assert constants.get_retrieval_top_k() == 15
