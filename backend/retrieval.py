import hashlib
import json
import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import chromadb
from cachetools import LRUCache
from google import genai
from google.genai import types as genai_types

from config import settings
from database import get_parent_chunks_by_ids
from key_pool import KEY_POOL, is_rate_limit_error

logger = logging.getLogger("notewave.retrieval")

# --- GEMINI EMBEDDING & CHROMA CLIENT ---
_EMBED_CLIENTS: Dict[str, genai.Client] = {}
_EMBED_CACHE: "LRUCache[str, List[float]]" = LRUCache(maxsize=settings.EMBED_CACHE_MAXSIZE)

def get_embed_client(api_key: str) -> genai.Client:
    if api_key not in _EMBED_CLIENTS:
        opts = genai_types.HttpOptions(retry_options=genai_types.HttpRetryOptions(attempts=1))
        _EMBED_CLIENTS[api_key] = genai.Client(api_key=api_key, http_options=opts)
    return _EMBED_CLIENTS[api_key]

def embed_texts(texts: List[str], api_key: Optional[str] = None, batch_size: int = 25) -> List[List[float]]:
    if not texts:
        return []
    keys = [api_key.strip()] if api_key and api_key.strip() else []
    keys.extend([k for k in KEY_POOL.keys if k not in keys])
    if not keys and KEY_POOL.has_keys():
        keys.append(KEY_POOL.primary())
    if not keys:
        raise ValueError("No Gemini API keys configured.")

    vectors: List[Optional[List[float]]] = [None] * len(texts)
    uncached_idx = []
    uncached_txt = []

    for i, t in enumerate(texts):
        h = hashlib.sha256(t.encode("utf-8")).hexdigest()
        if h in _EMBED_CACHE:
            vectors[i] = _EMBED_CACHE[h]
        else:
            uncached_idx.append(i)
            uncached_txt.append(t)

    if not uncached_txt:
        return [v for v in vectors if v is not None]

    for start in range(0, len(uncached_txt), batch_size):
        batch = uncached_txt[start : start + batch_size]
        last_err = None
        for key in keys:
            try:
                client = get_embed_client(key)
                res = client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=batch,
                    config=genai_types.EmbedContentConfig(output_dimensionality=settings.EMBEDDING_DIM),
                )
                for local_i, emb in enumerate(res.embeddings):
                    orig_i = uncached_idx[start + local_i]
                    vectors[orig_i] = emb.values
                    _EMBED_CACHE[hashlib.sha256(batch[local_i].encode("utf-8")).hexdigest()] = emb.values
                last_err = None
                break
            except Exception as e:
                last_err = e
                if is_rate_limit_error(e):
                    time.sleep(1.0)
                    continue
                raise e
        if last_err:
            raise last_err

    return [v for v in vectors if v is not None]

# --- CHROMA VECTOR STORE ---
class ChromaStore:
    def __init__(self, persist_dir: str = settings.CHROMA_DIR):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="notewave_knowledge",
            metadata={"hnsw:space": "cosine", "embedding_dim": str(settings.EMBEDDING_DIM)},
        )

    def upsert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        if not chunks:
            return 0
        ids = [c["id"] for c in chunks]
        docs = [c["text"] for c in chunks]
        metas = []
        for c in chunks:
            m = {}
            for k, v in c.get("metadata", {}).items():
                m[k] = v if isinstance(v, (str, int, float, bool)) else str(v)
            metas.append(m)

        for i in range(0, len(ids), 100):
            self.collection.upsert(
                ids=ids[i : i + 100],
                documents=docs[i : i + 100],
                embeddings=embeddings[i : i + 100],
                metadatas=metas[i : i + 100],
            )
        return len(chunks)

    def search(
        self,
        query_vector: List[float],
        k: int = settings.TOP_K_CANDIDATES,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if metadata_filter:
            kwargs["where"] = metadata_filter

        res = self.collection.query(**kwargs)
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        ids = (res.get("ids") or [[]])[0]

        candidates = []
        for chunk_id, text, meta, dist in zip(ids, docs, metas, dists):
            sim = round(1.0 - float(dist), 4) if dist is not None else 0.0
            candidates.append({
                "id": chunk_id,
                "text": text,
                "metadata": meta or {},
                "score": sim,
            })
        return candidates

    def delete_document(self, filename: str):
        try:
            self.collection.delete(where={"source_filename": filename})
        except Exception:
            pass

chroma_db = ChromaStore()

# --- BM25 KEYWORD SEARCH INDEX ---
class BM25Index:
    """Persistent and synchronized BM25 keyword search index."""

    def __init__(self, index_file: str = os.path.join(settings.CHROMA_DIR, "bm25_corpus.json")):
        self.index_file = index_file
        self.chunks: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25 = None
        self._lock = threading.RLock()
        self._load()

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\w+", text)]

    def _load(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                self.tokenized_corpus = [self._tokenize(c["text"]) for c in self.chunks]
                if self.tokenized_corpus:
                    from rank_bm25 import BM25Plus
                    self.bm25 = BM25Plus(self.tokenized_corpus)
                logger.info(f"Loaded BM25 index with {len(self.chunks)} chunks.")
            except Exception as e:
                logger.warning(f"Could not load BM25 index: {e}")

    def _save(self):
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not save BM25 index: {e}")

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        with self._lock:
            new_ids = {c["id"] for c in new_chunks}
            self.chunks = [c for c in self.chunks if c["id"] not in new_ids]
            self.chunks.extend(new_chunks)
            self.tokenized_corpus = [self._tokenize(c["text"]) for c in self.chunks]
            if self.tokenized_corpus:
                from rank_bm25 import BM25Plus
                self.bm25 = BM25Plus(self.tokenized_corpus)
            self._save()

    def delete_document(self, filename: str):
        with self._lock:
            self.chunks = [c for c in self.chunks if c.get("metadata", {}).get("source_filename") != filename]
            self.tokenized_corpus = [self._tokenize(c["text"]) for c in self.chunks]
            if self.tokenized_corpus:
                from rank_bm25 import BM25Plus
                self.bm25 = BM25Plus(self.tokenized_corpus)
            else:
                self.bm25 = None
            self._save()

    def search(
        self,
        query: str,
        k: int = settings.TOP_K_CANDIDATES,
        filename_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            if not self.bm25 or not self.chunks:
                return []

            tokens = self._tokenize(query)
            if not tokens:
                return []

            query_set = set(tokens)
            scores = self.bm25.get_scores(tokens)
            scored_pairs = []
            for idx, score in enumerate(scores):
                c = self.chunks[idx]
                if filename_filter and c.get("metadata", {}).get("source_filename") != filename_filter:
                    continue
                doc_tokens = self.tokenized_corpus[idx]
                overlap = query_set.intersection(doc_tokens)
                if overlap:
                    final_score = float(score) if score > 0 else float(len(overlap))
                    scored_pairs.append((final_score, c))

            scored_pairs.sort(key=lambda x: x[0], reverse=True)
            results = []
            for score, c in scored_pairs[:k]:
                results.append({
                    "id": c["id"],
                    "text": c["text"],
                    "metadata": c.get("metadata", {}),
                    "score": float(score),
                })
            return results

bm25_index = BM25Index()

# --- CROSS-ENCODER RERANKER ---
class CrossEncoderSingleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrossEncoderSingleton, cls).__new__(cls)
            cls._instance.model = None
            cls._instance._failed = False
        return cls._instance

    def get_model(self):
        if self.model is None and not self._failed:
            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(settings.RERANKER_MODEL, max_length=512)
                logger.info(f"Cross-encoder '{settings.RERANKER_MODEL}' loaded.")
            except Exception as e:
                logger.error(f"Failed to load CrossEncoder: {e}")
                self._failed = True
        return self.model

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = settings.TOP_K_FINAL) -> List[Dict[str, Any]]:
        if not candidates:
            return []
        model = self.get_model()
        if model is None or not settings.RERANKER_ENABLED:
            return candidates[:top_k]

        pairs = [[query, c["text"][:1000]] for c in candidates]
        scores = model.predict(pairs, batch_size=16)
        for c, s in zip(candidates, scores):
            c["cross_score"] = float(s)

        sorted_c = sorted(candidates, key=lambda x: x.get("cross_score", 0.0), reverse=True)
        return sorted_c[:top_k]

reranker = CrossEncoderSingleton()

# --- INTELLIGENT QUERY REWRITING ---
def rewrite_query(query: str, api_key: Optional[str] = None) -> Tuple[str, List[str], float]:
    """
    Intelligently rewrites queries: fixes typos, expands technical abbreviations,
    and clarifies intent while strictly preserving proper names, technical terms, and IDs.
    Returns: (rewritten_query, search_variants, latency_ms)
    """
    t0 = time.perf_counter()
    trimmed = query.strip()
    words = trimmed.split()

    # Skip rewriting for short or unambiguous technical queries
    if len(words) <= 2 and (trimmed.isupper() or len(trimmed) < 12):
        return trimmed, [trimmed], 0.0

    prompt = (
        "You are an expert search query optimizer for technical and academic documents.\n"
        "Your task is to rewrite the user's query to fix spelling errors, expand obvious abbreviations, "
        "and clarify user intent for search retrieval.\n"
        "RULES:\n"
        "1. PRESERVE all technical terms, names, product names, numbers, codes, and quoted text exactly.\n"
        "2. Do NOT invent concepts, facts, or assumptions not implied by the query.\n"
        "3. Output ONLY the rewritten search query. No markdown, no quotes, no explanations.\n\n"
        f"User Query: {trimmed}\n"
        "Optimized Query:"
    )

    try:
        keys = [api_key.strip()] if api_key and api_key.strip() else []
        keys.extend([k for k in KEY_POOL.keys if k not in keys])
        if not keys and KEY_POOL.has_keys():
            keys.append(KEY_POOL.primary())
        if not keys:
            return trimmed, [trimmed], 0.0

        client = get_embed_client(keys[0])
        resp = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=60,
            ),
        )
        rewritten = (resp.text or "").strip()
        latency = round((time.perf_counter() - t0) * 1000.0, 2)
        if rewritten and len(rewritten) > 2:
            return rewritten, [trimmed, rewritten], latency
    except Exception as e:
        logger.debug(f"Query rewrite skipped/failed: {e}")

    latency = round((time.perf_counter() - t0) * 1000.0, 2)
    return trimmed, [trimmed], latency

# --- HYBRID RETRIEVAL PIPELINE WITH RRF FUSION & PARENT EXPANSION ---
def reciprocal_rank_fusion(
    semantic_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = settings.RRF_K,
) -> List[Dict[str, Any]]:
    """Combines semantic search and BM25 rankings using Reciprocal Rank Fusion."""
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    # 1. Score semantic results by rank (1-indexed)
    for rank, item in enumerate(semantic_results, start=1):
        doc_id = item["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
        if doc_id not in doc_map:
            doc_map[doc_id] = dict(item)

    # 2. Score BM25 results by rank (1-indexed)
    for rank, item in enumerate(bm25_results, start=1):
        doc_id = item["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
        if doc_id not in doc_map:
            doc_map[doc_id] = dict(item)

    # 3. Sort candidates by fused score
    fused = []
    for doc_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
        entry = doc_map[doc_id]
        entry["rrf_score"] = round(score, 6)
        fused.append(entry)
    return fused

def hybrid_retrieve(
    query: str,
    api_key: Optional[str] = None,
    filename_filter: Optional[str] = None,
    top_k_candidates: int = settings.TOP_K_CANDIDATES,
    top_k_final: int = settings.TOP_K_FINAL,
) -> Dict[str, Any]:
    """
    Executes complete Hybrid Retrieval:
    User Query -> Query Rewriting -> Semantic + BM25 Search -> RRF Fusion ->
    Cross-Encoder Reranking -> Parent Section Expansion -> Compact Context
    """
    timings: Dict[str, float] = {}
    t_start = time.perf_counter()

    # 1. Query Rewriting
    rewritten_q, variants, rewrite_ms = rewrite_query(query, api_key=api_key)
    timings["rewrite_ms"] = rewrite_ms

    # 2. BM25 Search (using both original query for exact matches + rewritten query)
    t0 = time.perf_counter()
    bm25_q = f"{query} {rewritten_q}".strip() if query != rewritten_q else query
    bm25_candidates = bm25_index.search(bm25_q, k=top_k_candidates, filename_filter=filename_filter)
    timings["bm25_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    # 3. Semantic Vector Search
    t0 = time.perf_counter()
    search_q = rewritten_q if rewritten_q else query
    try:
        q_vec = embed_texts([search_q], api_key=api_key)[0]
        meta_filter = {"source_filename": filename_filter.strip()} if filename_filter else None
        semantic_candidates = chroma_db.search(q_vec, k=top_k_candidates, metadata_filter=meta_filter)
    except Exception as e:
        logger.warning(f"Vector search failed: {e}. Relying on BM25.")
        semantic_candidates = []
    timings["semantic_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    # 4. Score Fusion (RRF) & Deduplication
    t0 = time.perf_counter()
    fused_candidates = reciprocal_rank_fusion(semantic_candidates, bm25_candidates, k=settings.RRF_K)
    timings["fusion_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    # 5. Cross-Encoder Re-Ranking
    t0 = time.perf_counter()
    best_children = reranker.rerank(query=search_q, candidates=fused_candidates, top_k=top_k_final)
    timings["rerank_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    # 6. Parent Context Expansion
    t0 = time.perf_counter()
    parent_ids = [c.get("metadata", {}).get("parent_id") for c in best_children if c.get("metadata", {}).get("parent_id")]
    parent_map = get_parent_chunks_by_ids(list(set(parent_ids)))

    seen_parents: Set[str] = set()
    context_blocks: List[str] = []

    for idx, c in enumerate(best_children, start=1):
        pid = c.get("metadata", {}).get("parent_id")
        meta = c.get("metadata", {})
        doc_name = meta.get("source_filename", "Document")
        page_num = meta.get("page_number", 1)
        section = meta.get("section_heading", "General")

        if pid and pid in parent_map and pid not in seen_parents:
            seen_parents.add(pid)
            parent_text = parent_map[pid]["text"].strip()
            header = f"[Evidence #{idx} | Source: {doc_name} | Page: {page_num} | Section: {section}]"
            context_blocks.append(f"{header}\n{parent_text}")
        elif not pid or pid not in parent_map:
            # Fallback to child text if parent record unavailable
            header = f"[Evidence #{idx} | Source: {doc_name} | Page: {page_num} | Section: {section}]"
            context_blocks.append(f"{header}\n{c['text'].strip()}")

    assembled_context = "\n\n---\n\n".join(context_blocks)
    timings["expansion_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
    timings["total_retrieval_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)

    return {
        "context": assembled_context,
        "passages": best_children,
        "rewritten_query": rewritten_q,
        "timings": timings,
        "bm25_count": len(bm25_candidates),
        "semantic_count": len(semantic_candidates),
        "fused_count": len(fused_candidates),
    }
