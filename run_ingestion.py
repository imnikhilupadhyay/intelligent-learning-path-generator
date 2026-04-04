"""Run the data pipeline: preprocess Excel → CSV → enrich → Chroma index."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(_SRC))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from ingestion.build_chroma import build_from_enriched_csv  # noqa: E402
from ingestion.enrich_course_master import run_enrichment  # noqa: E402
from ingestion.preprocess_data import run_default_preprocess  # noqa: E402


def main() -> None:
    """Execute ingestion steps in workflow order."""
    try:
        run_default_preprocess()
        run_enrichment()
        build_from_enriched_csv()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
