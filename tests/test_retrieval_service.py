"""Retrieval keyword leg tests (Chroma optional)."""

from __future__ import annotations

import pandas as pd

from services.retrieval_service import RetrievalService


def test_keyword_candidates_finds_java() -> None:
    """Keyword retrieval surfaces skill-aligned rows."""
    df = pd.DataFrame(
        [
            {
                "Course ID": 1,
                "Course Full Name": "Java Threads",
                "summary": "Concurrency for Java developers",
            },
            {
                "Course ID": 2,
                "Course Full Name": "Banking 101",
                "summary": "Finance basics",
            },
        ],
    )
    svc = RetrievalService(chroma_path="")  # chroma path unused for keyword-only
    ids = svc.keyword_candidates(df, "Application Services", "Java", top_k=5)
    assert 1 in ids
