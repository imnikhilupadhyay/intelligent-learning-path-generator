"""Optional RAGAS evaluation harness (requires API keys and labeled JSONL)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_SRC_ROOT = Path(__file__).resolve().parents[1]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from utils.logging_utils import get_logger

logger = get_logger(__name__)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSON lines evaluation set.

    Args:
        path: Path to ``.jsonl`` file.

    Returns:
        List of records.
    """
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def run_ragas_synthetic_note() -> str:
    """Return guidance string; full RAGAS run is environment-dependent.

    Returns:
        Human-readable instructions.
    """
    return (
        "RAGAS metrics (faithfulness, answer relevancy, context precision/recall) should be run "
        "with your chosen LLM/embeddings providers. Populate src/evaluation/datasets/eval_records.jsonl "
        "using the schema from workflow.md section 12.4, then install ragas and execute a small "
        "LangChain-style evaluation loop against your retrieval and explanation outputs."
    )


if __name__ == "__main__":
    logger.info(run_ragas_synthetic_note())
