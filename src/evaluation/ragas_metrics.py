"""RAGAS-style scores from a stored session payload (optional LLM/embeddings)."""

from __future__ import annotations

import os
from typing import Any

RAGAS_METRIC_DESCRIPTIONS: dict[str, str] = {
    "faithfulness": (
        "Measures whether the answer is grounded in the retrieved contexts — "
        "claims should be supported by the provided course snippets, not invented."
    ),
    "answer_relevancy": (
        "Measures how well the answer addresses the evaluation question "
        "(relevance of the plan/explanation to what was asked)."
    ),
    "context_precision": (
        "Share of retrieved contexts that are relevant to the question. "
        "Higher means less noise in retrieved course text."
    ),
    "context_recall": (
        "Whether the contexts cover the information needed to answer well. "
        "Often needs a reference answer (ground truth) for a strict score."
    ),
}


def _scores_dict_from_ragas_result(result: Any) -> dict[str, float]:
    """Normalize ragas ``evaluate`` output to ``metric_name -> float``."""
    out: dict[str, float] = {}
    if result is None:
        return out
    repr_dict = getattr(result, "_repr_dict", None)
    if isinstance(repr_dict, dict):
        for k, v in repr_dict.items():
            try:
                fv = float(v)
                if fv == fv:
                    out[str(k)] = fv
            except (TypeError, ValueError):
                continue
        if out:
            return out
    if hasattr(result, "to_pandas"):
        try:
            df = result.to_pandas()
            if df is not None and len(df) > 0:
                row = df.iloc[0]
                for col in df.columns:
                    try:
                        v = float(row[col])
                        if v == v:  # not NaN
                            out[str(col)] = v
                    except (TypeError, ValueError):
                        continue
        except Exception:  # noqa: BLE001
            pass
    if isinstance(result, dict):
        for k, v in result.items():
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
    return out


def _openai_api_key() -> str:
    """Return a non-empty API key from common env vars, or empty string."""
    for name in ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY"):
        v = (os.environ.get(name) or "").strip()
        if v:
            return v
    return ""


def _legacy_faithfulness_answer_relevancy_metrics() -> tuple[list[Any], str | None]:
    """Return pre-built metric objects compatible with ``ragas.evaluate``.

    RAGAS 0.4 ``evaluate()`` only accepts instances of ``ragas.metrics.base.Metric``.
    The classes under ``ragas.metrics.collections`` use a different base and are
    rejected with "All metrics must be initialised metric objects". The stable
    integration path is the legacy module-level ``faithfulness`` and
    ``answer_relevancy`` singletons, with ``llm`` / ``embeddings`` passed into
    ``evaluate()``.

    Returns:
        Tuple of ``(metrics, error_message)``.
    """
    try:
        from ragas.metrics._answer_relevance import answer_relevancy
        from ragas.metrics._faithfulness import faithfulness
    except ImportError as exc:
        return [], f"Could not import legacy RAGAS metrics: {exc}"
    return [faithfulness, answer_relevancy], None


def _build_ragas_evaluate_llm_and_embeddings() -> tuple[Any, Any, str | None]:
    """Build ``llm`` and LangChain embeddings for ``ragas.evaluate``.

    Legacy ``answer_relevancy`` expects LangChain-style ``embed_query`` /
    ``embed_documents``, so we use ``langchain_openai.embeddings.OpenAIEmbeddings``.
    Uses ``RAGAS_LLM_MODEL`` (default ``gpt-4o-mini``) separately from
    ``OPENAI_MODEL`` (e.g. o-series).

    Returns:
        ``(llm, langchain_embeddings, error)``.
    """
    if not _openai_api_key():
        return (
            None,
            None,
            "OPENAI_API_KEY or AZURE_OPENAI_API_KEY is required for RAGAS metrics.",
        )
    try:
        from openai import OpenAI
    except ImportError as exc:
        return None, None, f"openai package required for RAGAS: {exc}"
    try:
        from langchain_openai.embeddings import OpenAIEmbeddings as LangchainOpenAIEmbeddings
    except ImportError as exc:
        return (
            None,
            None,
            f"langchain-openai required for answer_relevancy metric: {exc}",
        )

    base_url = (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip()
    llm_model = (os.environ.get("RAGAS_LLM_MODEL") or "gpt-4o-mini").strip()
    emb_model = (os.environ.get("RAGAS_EMBEDDING_MODEL") or "text-embedding-3-small").strip()

    try:
        client = OpenAI(api_key=_openai_api_key(), base_url=base_url)
        from ragas.llms import llm_factory

        llm = llm_factory(llm_model, client=client)
        emb_kwargs: dict[str, Any] = {
            "model": emb_model,
            "openai_api_key": _openai_api_key(),
        }
        if base_url:
            emb_kwargs["openai_api_base"] = base_url
        lc_embeddings = LangchainOpenAIEmbeddings(**emb_kwargs)
        return llm, lc_embeddings, None
    except Exception as exc:  # noqa: BLE001
        return None, None, f"Failed to configure RAGAS LLM/embeddings: {exc}"


def compute_ragas_scores(session_payload: dict[str, Any]) -> dict[str, Any]:
    """Run RAGAS metrics on ``ragas_evaluation_inputs`` inside a session JSON.

    Args:
        session_payload: Full object saved as ``session_runs/<run_id>_session.json``.

    Returns:
        Dict with ``scores``, ``metric_descriptions``, optional ``error``, and ids.
    """
    run_id = session_payload.get("run_id")
    portal_id = session_payload.get("portal_id")
    base_out: dict[str, Any] = {
        "run_id": run_id,
        "portal_id": portal_id,
        "scores": {},
        "metric_descriptions": RAGAS_METRIC_DESCRIPTIONS,
        "error": None,
    }
    inputs = session_payload.get("ragas_evaluation_inputs") or {}
    question = (inputs.get("question") or "").strip()
    answer = (inputs.get("answer") or "").strip()
    contexts = inputs.get("contexts") or []
    if not isinstance(contexts, list):
        contexts = [str(contexts)]
    contexts = [str(c) for c in contexts if str(c).strip()]
    if not question or not answer:
        base_out["error"] = "Session is missing ragas_evaluation_inputs.question or .answer."
        return base_out
    if not contexts:
        contexts = ["(empty context)"]

    try:
        from datasets import Dataset
    except ImportError as exc:
        base_out["error"] = f"datasets package required: {exc}"
        return base_out

    try:
        from ragas import evaluate as ragas_evaluate
    except ImportError as exc:
        base_out["error"] = f"ragas package required: {exc}"
        return base_out

    # RAGAS single-turn metrics expect these column names (v0.2+).
    ds = Dataset.from_dict(
        {
            "user_input": [question],
            "response": [answer],
            "retrieved_contexts": [contexts],
        },
    )

    metrics, imp_err = _legacy_faithfulness_answer_relevancy_metrics()
    if imp_err:
        base_out["error"] = imp_err
        return base_out

    llm, lc_embeddings, cfg_err = _build_ragas_evaluate_llm_and_embeddings()
    if cfg_err:
        base_out["error"] = cfg_err
        return base_out

    try:
        result = ragas_evaluate(
            ds,
            metrics=metrics,
            llm=llm,
            embeddings=lc_embeddings,
        )
        base_out["scores"] = _scores_dict_from_ragas_result(result)
    except Exception as exc:  # noqa: BLE001
        base_out["error"] = f"RAGAS evaluate failed: {exc}"
        return base_out

    if not base_out["scores"]:
        base_out["error"] = (
            "RAGAS returned no numeric scores (check OPENAI_API_KEY and ragas/embeddings setup)."
        )
    return base_out
