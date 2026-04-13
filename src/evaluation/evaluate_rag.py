"""Compare retrieval strategies (keyword-only vs hybrid). Placeholder for experiments."""

from __future__ import annotations

from typing import Callable, Sequence


def compare_strategies(
    strategies: dict[str, Callable[[], Sequence[int]]],
) -> dict[str, list[int]]:
    """Run named retrieval strategies and return their course-id lists.

    Args:
        strategies: Map strategy name to callable returning course ids.

    Returns:
        Strategy name to id list.
    """
    return {name: list(fn()) for name, fn in strategies.items()}
