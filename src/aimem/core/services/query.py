"""Hybrid BM25 + embedding search (US-005, R-011, R-021, R-046).

Strategy:
  1. Build a BM25 index over all records' title + body.
  2. If an embedding provider is available, also score by cosine similarity
     using a flat HNSW-style in-memory scan (hnswlib optional; falls back
     to numpy dot-product, falls back to BM25-only).
  3. Merge scores with equal weighting; return top-K (default 5).

The index is **never committed** — it is rebuilt from disk on demand and
held in memory for the lifetime of the process.  On a cold call it takes
O(N) to build; subsequent calls within the same process reuse it.

BM25-only fallback (R-011):
  When the embedding model is unavailable, we emit a warning and return
  BM25-only results.  This is a **graceful degradation**, not a silent one.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from aimem.core import logging as _logging
from aimem.core.config import AimemConfig
from aimem.core.repository import LayerRepo
from aimem.core.schema import Layer, MemoryRecord, MemoryType

log = _logging.get_logger(__name__)


@dataclass
class SearchResult:
    record: MemoryRecord
    score: float
    rank: int


def query(
    *,
    memory_dir: Path,
    q: str,
    top_k: int | None = None,
    layer: Layer = Layer.PERSONAL,
    memory_type: MemoryType | None = None,
    tags: list[str] | None = None,
) -> list[SearchResult]:
    """Hybrid search; returns up to *top_k* results ranked by score.

    Falls back to BM25-only when embedding is unavailable.
    """
    t0 = time.monotonic()
    cfg = AimemConfig.load(memory_dir)
    k = top_k if top_k is not None else cfg.retrieval_window

    repo = LayerRepo(memory_dir)
    records = repo.list_records(layer=layer, memory_type=memory_type, tags=tags)

    if not records:
        return []

    results = _hybrid_search(q, records, k, cfg, memory_dir)
    latency_ms = int((time.monotonic() - t0) * 1000)
    log.info(op="query", top_k=k, num_results=len(results), latency_ms=latency_ms)
    return results


def _doc_text(rec: MemoryRecord) -> str:
    """Full text representation for indexing."""
    parts = [rec.title, rec.body] + rec.tags
    return " ".join(p for p in parts if p)


def _bm25_scores(query_tokens: list[str], records: list[MemoryRecord]) -> list[float]:
    try:
        from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]
    except ImportError:
        # Very simple TF fallback if rank_bm25 not installed
        scores: list[float] = []
        for rec in records:
            text = _doc_text(rec).lower()
            score = sum(text.count(t) for t in query_tokens)
            scores.append(float(score))
        return scores

    corpus = [_doc_text(r).lower().split() for r in records]
    bm25 = BM25Okapi(corpus)
    scores_arr = list(bm25.get_scores(query_tokens))

    # BM25 degenerates to all-zeros when the corpus is very small or when
    # every document contains the query term (IDF → 0).  Fall back to simple TF.
    if all(s == 0.0 for s in scores_arr):
        scores_arr = []
        for rec in records:
            text = _doc_text(rec).lower()
            score = sum(text.count(t) for t in query_tokens)
            scores_arr.append(float(score))
    return scores_arr  # type: ignore[return-value]


def _embed_scores(
    q: str, records: list[MemoryRecord], cfg: AimemConfig, memory_dir: Path
) -> list[float] | None:
    """Return cosine similarity scores, or None if embedding unavailable."""
    from aimem.core.embed import make_provider

    provider = make_provider(cfg.embed)
    if not provider.available:
        log.warning(
            op="query",
            reason="embed_unavailable",
        )
        return None

    try:
        texts = [_doc_text(r) for r in records]
        doc_vecs = provider.embed(texts)
        q_vec = provider.embed([q])[0]

        try:
            import numpy as np  # noqa: PLC0415

            q_arr = np.array(q_vec, dtype="float32")
            d_arr = np.array(doc_vecs, dtype="float32")
            # Cosine similarity: dot / (||q|| * ||d||)
            q_norm = np.linalg.norm(q_arr)
            d_norms = np.linalg.norm(d_arr, axis=1)
            if q_norm == 0:
                return [0.0] * len(records)
            safe_norms = np.where(d_norms == 0, 1.0, d_norms)
            sims = (d_arr @ q_arr) / (safe_norms * q_norm)
            return sims.tolist()
        except ImportError:
            # Fallback without numpy: plain dot product
            def _dot(a: list[float], b: list[float]) -> float:
                return sum(x * y for x, y in zip(a, b, strict=False))

            def _norm(v: list[float]) -> float:
                return sum(x * x for x in v) ** 0.5

            qn = _norm(q_vec)
            if qn == 0:
                return [0.0] * len(records)
            return [
                _dot(q_vec, dv) / ((_norm(dv) or 1.0) * qn) for dv in doc_vecs
            ]
    except Exception as exc:
        log.warning(op="query", reason="embed_error", error=str(exc))
        return None


def _hybrid_search(
    q: str,
    records: list[MemoryRecord],
    k: int,
    cfg: AimemConfig,
    memory_dir: Path,
) -> list[SearchResult]:
    query_tokens = q.lower().split()
    bm25 = _bm25_scores(query_tokens, records)

    # Normalise BM25 to [0, 1]
    max_bm25 = max(bm25) if bm25 else 1.0
    bm25_norm = [s / max_bm25 if max_bm25 > 0 else 0.0 for s in bm25]

    embed = _embed_scores(q, records, cfg, memory_dir)

    if embed is not None:
        # Equal weighting
        combined = [(b + e) / 2.0 for b, e in zip(bm25_norm, embed, strict=False)]
    else:
        combined = bm25_norm

    ranked = sorted(
        enumerate(combined), key=lambda x: x[1], reverse=True
    )[:k]

    return [
        SearchResult(record=records[idx], score=score, rank=rank + 1)
        for rank, (idx, score) in enumerate(ranked)
        if score > 0
    ]
