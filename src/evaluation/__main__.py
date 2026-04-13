"""Run evaluation demos.

Either:

- ``python -m evaluation`` with ``PYTHONPATH=src`` (repo root), or
- ``python src/evaluation/__main__.py`` from the repo root (path is fixed below).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[1]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from evaluation.evaluate_rule_engine import (
    completed_exclusion_accuracy,
    practice_keyword_precision,
    training_goal_coverage,
)
from evaluation.ragas_runner import run_ragas_synthetic_note


def main() -> None:
    """Print toy scores for rule-engine helpers and RAGAS setup notes."""
    print("=== Rule-engine metrics (library demo; extend with your labeled fixtures) ===")
    print(
        "completed_exclusion_accuracy (no leak):",
        round(completed_exclusion_accuracy([10, 11], {9}), 4),
    )
    print(
        "completed_exclusion_accuracy (one leak):",
        round(completed_exclusion_accuracy([10, 9], {9}), 4),
    )
    print(
        "training_goal_coverage (8h / 16h goal):",
        round(training_goal_coverage(8.0, 16.0), 4),
    )
    print(
        "practice_keyword_precision:",
        round(practice_keyword_precision(["Java threads introduction"], ["java", "threads"]), 4),
    )
    print()
    print("=== RAG / RAGAS ===")
    print(run_ragas_synthetic_note())


if __name__ == "__main__":
    main()
