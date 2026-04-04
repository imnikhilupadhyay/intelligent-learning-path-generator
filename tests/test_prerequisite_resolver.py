"""Prerequisite parsing tests."""

from __future__ import annotations

import pandas as pd

from planning.prerequisite_resolver import extract_prerequisite_text, map_prerequisite_to_course_id


def test_extract_prerequisite() -> None:
    """Regex picks prerequisite clause."""
    s = "Prerequisite: Knowledge of Java. Audience: developers."
    assert extract_prerequisite_text(s) == "Knowledge of Java"


def test_map_to_catalog() -> None:
    """Fuzzy map prerequisite text to catalog row."""
    df = pd.DataFrame(
        [
            {"Course ID": 1, "Course Full Name": "Java Basics"},
            {"Course ID": 2, "Course Full Name": "Advanced Threads"},
        ],
    )
    mid, note = map_prerequisite_to_course_id("Java Basics Workshop", df)
    assert mid == 1
    assert note is not None
