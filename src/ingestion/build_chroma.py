"""Build or refresh the persistent Chroma course collection."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[1]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import chromadb
import pandas as pd

from utils.constants import (
    CHROMA_DIR,
    COL_COURSE_FULL_NAME,
    COL_COURSE_ID,
    COL_SUMMARY,
    COURSE_MASTER_ENRICHED_CSV,
    RETRIEVAL_CONFIG_YAML,
)
from utils.file_utils import load_yaml_cached
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def _collection_name() -> str:
    cfg = load_yaml_cached(RETRIEVAL_CONFIG_YAML)
    return str(cfg.get("chroma_collection_name", "course_master_collection"))


def build_from_enriched_csv(
    csv_path: str | None = None,
    chroma_path: str | None = None,
) -> None:
    """Upsert course documents into Chroma from the enriched CSV.

    Args:
        csv_path: Enriched CSV path.
        chroma_path: Persistent Chroma directory.
    """
    path = csv_path or str(COURSE_MASTER_ENRICHED_CSV)
    persist = chroma_path or os.environ.get("CHROMA_DB_PATH") or str(CHROMA_DIR)
    os.makedirs(persist, exist_ok=True)
    df = pd.read_csv(path)
    client = chromadb.PersistentClient(path=persist)
    name = _collection_name()
    try:
        client.delete_collection(name)
    except Exception:  # noqa: BLE001
        pass
    coll = client.create_collection(name=name, metadata={"source": "course_master_enriched"})

    documents: list[str] = []
    ids: list[str] = []
    metadatas: list[dict] = []

    for _, row in df.iterrows():
        try:
            cid = int(float(row.get(COL_COURSE_ID)))
        except (TypeError, ValueError):
            continue
        title = str(row.get(COL_COURSE_FULL_NAME, "") or "")
        summary = str(row.get(COL_SUMMARY, "") or "")
        topics = []
        for col in ("parsed_audience_text", "parsed_grade_hint"):
            v = row.get(col)
            if pd.notna(v) and str(v).strip():
                topics.append(str(v))
        doc = (
            f"Course ID: {cid}\nCourse Full Name: {title}\nSummary: {summary}\n"
            f"Parsed Topics: {', '.join(topics)}\n"
            f"Parsed Prerequisite: {row.get('parsed_prerequisite_text', '')}\n"
            f"Parsed Duration Hours: {row.get('parsed_duration_hours', '')}\n"
        )
        documents.append(doc)
        ids.append(str(cid))
        metadatas.append(
            {
                "course_id": str(cid),
                "course_name": title[:256],
                "source": "course_master",
            },
        )
    batch = 128
    for i in range(0, len(documents), batch):
        coll.add(
            ids=ids[i : i + batch],
            documents=documents[i : i + batch],
            metadatas=metadatas[i : i + batch],
        )
    logger.info("Indexed %s courses into Chroma at %s", len(documents), persist)


if __name__ == "__main__":
    build_from_enriched_csv()
