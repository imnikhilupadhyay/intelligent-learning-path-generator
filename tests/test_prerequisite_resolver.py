"""Prerequisite parsing tests."""

from __future__ import annotations

import pandas as pd

from planning.prerequisite_resolver import (
    PrerequisiteParseResult,
    build_ordered_ids_with_prereqs,
    extract_prerequisite_text,
    map_prerequisite_to_course_id,
)


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


def test_build_ordered_ids_breaks_prerequisite_cycle() -> None:
    """Cyclic prereq mappings must not recurse infinitely."""
    # 1 → 2 → 3 → 1
    prereq_map = {
        1: PrerequisiteParseResult("b", 2, None),
        2: PrerequisiteParseResult("c", 3, None),
        3: PrerequisiteParseResult("a", 1, None),
    }
    ordered = build_ordered_ids_with_prereqs([1], prereq_map, completed_ids=set())
    assert set(ordered) == {1, 2, 3}
    assert len(ordered) == 3


def test_self_prerequisite_ignored_in_chain() -> None:
    """Course mapped as its own prerequisite should not recurse."""
    prereq_map = {
        9: PrerequisiteParseResult("self", 9, None),
    }
    assert build_ordered_ids_with_prereqs([9], prereq_map, completed_ids=set()) == [9]
