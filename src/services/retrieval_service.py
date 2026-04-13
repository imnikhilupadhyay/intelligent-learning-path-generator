"""Hybrid keyword + Chroma retrieval over the course catalog."""

from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

import chromadb
import pandas as pd

from services.practice_mapper import build_retrieval_query_phrase
from utils.constants import (
    CHROMA_DIR,
    COL_COURSE_FULL_NAME,
    COL_COURSE_ID,
    COL_SUMMARY,
    RETRIEVAL_CONFIG_YAML,
)
from utils.file_utils import load_yaml_cached
from utils.logging_utils import get_logger
from utils.text_utils import lowercase_copy

logger = get_logger(__name__)


def _retrieval_cfg() -> Mapping[str, Any]:
    return load_yaml_cached(RETRIEVAL_CONFIG_YAML)


def _collection_name() -> str:
    return str(_retrieval_cfg().get("chroma_collection_name", "course_master_collection"))


class RetrievalService:
    """Query Chroma and merge with rule-based keyword matches."""

    def __init__(
        self,
        chroma_path: str | None = None,
        course_df: pd.DataFrame | None = None,
    ) -> None:
        """Initialize retrieval service."""
        path = chroma_path or os.environ.get("CHROMA_DB_PATH") or str(CHROMA_DIR)
        self._chroma_path = path
        self._course_df = course_df
        self._client: chromadb.PersistentClient | None = None
        self._collection = None

    def _get_collection(self):
        if self._client is None:
            os.makedirs(self._chroma_path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self._chroma_path)
        if self._collection is None:
            self._collection = self._client.get_or_create_collection(name=_collection_name())
        return self._collection

    def keyword_candidates(
        self,
        df: pd.DataFrame,
        practice_raw: str | None,
        target_expertise: str | None,
        top_k: int,
    ) -> list[int]:
        """Return course ids scoring by simple keyword overlap."""
        from services.practice_mapper import skills_for_practice

        skills = skills_for_practice(practice_raw)
        tokens: list[str] = [lowercase_copy(s) for s in skills if s]
        if target_expertise:
            tokens.append(lowercase_copy(target_expertise))
        if not tokens:
            return []
        scores: list[tuple[int, int]] = []
        id_col, name_col, sum_col = COL_COURSE_ID, COL_COURSE_FULL_NAME, COL_SUMMARY
        for _, row in df.iterrows():
            try:
                cid = int(float(row.get(id_col)))
            except (TypeError, ValueError):
                continue
            text = f"{row.get(name_col, '')} {row.get(sum_col, '')}"
            h = lowercase_copy(str(text))
            hit = sum(1 for t in tokens if t and t in h)
            if hit > 0:
                scores.append((cid, hit))
        scores.sort(key=lambda x: -x[1])
        return [c for c, _ in scores[: max(top_k, 1)]]

    def semantic_candidates(self, query: str, top_k: int) -> tuple[list[int], dict[int, float]]:
        """Query Chroma for similar courses.

        Returns:
            Tuple of course ids and approximate similarity map in [0,1].
        """
        col = self._get_collection()
        try:
            res = col.query(query_texts=[query], n_results=max(1, top_k))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Chroma query failed, semantic leg disabled: %s", exc)
            return [], {}
        ids_out: list[int] = []
        dist_map: dict[int, float] = {}
        meta_ids = res.get("ids") or []
        distances = res.get("distances") or []
        if not meta_ids or not meta_ids[0]:
            return [], {}
        raw_ids = meta_ids[0]
        raw_dists = distances[0] if distances and distances[0] else []
        for i, sid in enumerate(raw_ids):
            try:
                cid = int(float(sid))
            except (TypeError, ValueError):
                continue
            ids_out.append(cid)
            if i < len(raw_dists):
                d = float(raw_dists[i])
                # chroma distance depends on space; map crudely to similarity
                sim = 1.0 / (1.0 + max(0.0, d))
                dist_map[cid] = sim
            else:
                dist_map[cid] = 0.5
        return ids_out, dist_map

    def hybrid_retrieve(
        self,
        df: pd.DataFrame,
        practice_raw: str | None,
        target_expertise: str | None,
        top_k: int,
    ) -> tuple[list[int], dict[int, float]]:
        """Merge semantic and keyword retrieval results."""
        query = build_retrieval_query_phrase(practice_raw, target_expertise)
        sem_ids, sem_map = self.semantic_candidates(query, top_k=top_k)
        key_ids = self.keyword_candidates(df, practice_raw, target_expertise, top_k=top_k)
        merged: list[int] = []
        seen: set[int] = set()
        for cid in sem_ids + key_ids:
            if cid not in seen:
                merged.append(cid)
                seen.add(cid)
        # fill semantic map for keyword-only ids
        for cid in merged:
            sem_map.setdefault(cid, 0.45)
        return merged[: max(top_k * 2, 1)], sem_map
