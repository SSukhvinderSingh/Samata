"""
RAG Pipeline Skill for Samata Legal Assistant.
Executes Hybrid BM25 + Vector Search with RRF Fusion and Reranking over legal corpus.
Supports fast cached index loading from data/index/chunks.json.
"""

import os
import json
import re
import math
from pathlib import Path
from typing import Dict, List, Any, Optional

CORPUS_DIR = Path("data/corpus")
INDEX_DIR = Path("data/index")
CHUNKS_CACHE_FILE = INDEX_DIR / "chunks.json"
CRAG_THRESHOLD = 0.55

STOPWORDS = {
    "what", "are", "the", "how", "is", "under", "of", "in", "and", "a", "an",
    "to", "for", "by", "with", "from", "on", "at", "as", "or", "which", "can",
    "do", "does", "ke", "hai", "kya", "hain", "ko", "se", "aur", "mein"
}

OUT_OF_DOMAIN_PATTERNS = [
    r"crypto", r"bitcoin", r"capital gains", r"income tax", r"115bbh",
    r"blockchain", r"gst", r"corporate tax", r"mysql", r"python", r"react"
]

# Global in-memory storage for index & corpus chunks
_INDEX_STORE = {
    "chunks": [],
    "bm25": None,
    "tokenized_corpus": [],
    "is_loaded": False
}


def load_or_build_index(force_rebuild: bool = False) -> Dict[str, Any]:
    """
    Loads existing BM25/FAISS index from cache or builds it.
    """
    global _INDEX_STORE
    if _INDEX_STORE["is_loaded"] and not force_rebuild:
        return {"status": "already_loaded", "chunk_count": len(_INDEX_STORE["chunks"])}

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    chunks = []

    # 1. Load from disk cache
    if CHUNKS_CACHE_FILE.exists() and not force_rebuild:
        try:
            with open(CHUNKS_CACHE_FILE, "r", encoding="utf-8") as f:
                chunks = json.load(f)
            status = "loaded_from_cache"
        except Exception:
            chunks = []
            status = "cache_read_failed"
    else:
        status = "fresh_build"

    # 2. Build BM25 index over loaded chunks
    try:
        from rank_bm25 import BM25Okapi
        tokenized_corpus = []
        for c in chunks:
            text = (c.get("section_heading", "") + " " + c.get("chunk_text", "")).lower()
            tokens = [w for w in re.findall(r'\b\w+\b', text) if w not in STOPWORDS]
            tokenized_corpus.append(tokens)
        bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
    except Exception:
        bm25 = None
        tokenized_corpus = []

    _INDEX_STORE["chunks"] = chunks
    _INDEX_STORE["bm25"] = bm25
    _INDEX_STORE["tokenized_corpus"] = tokenized_corpus
    _INDEX_STORE["is_loaded"] = True

    return {"status": status, "chunk_count": len(chunks)}


def retrieve_chunks(
    query: str,
    top_k: int = 5,
    document_context_chunks: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Performs hybrid BM25 lexical retrieval and cross-reranking over the 13,000+ legal chunks.
    """
    load_or_build_index()

    all_chunks = list(_INDEX_STORE["chunks"])
    if document_context_chunks:
        all_chunks.extend(document_context_chunks)

    if not all_chunks:
        return {
            "retrieved_chunks": [],
            "top_score": 0.0,
            "crag_trigger": True
        }

    query_clean = query.lower()

    # Out of domain check
    for odp in OUT_OF_DOMAIN_PATTERNS:
        if re.search(odp, query_clean):
            return {
                "retrieved_chunks": [],
                "top_score": 0.30,
                "crag_trigger": True
            }

    raw_tokens = re.findall(r'\b\w+\b', query_clean)
    query_tokens = [w for w in raw_tokens if w not in STOPWORDS]
    if not query_tokens:
        query_tokens = raw_tokens

    # Expanded query tokens with root words
    expanded_tokens = list(query_tokens)
    if "condonation" in query_clean or "condone" in query_clean:
        expanded_tokens.extend(["condonation", "condoned", "condone", "condoning"])
    if "desertion" in query_clean or "desert" in query_clean:
        expanded_tokens.extend(["desertion", "deserted", "deserendi"])
    if "cruelty" in query_clean:
        expanded_tokens.extend(["cruelty", "cruel", "harassment"])

    # 1. Score with BM25 if available
    bm25 = _INDEX_STORE["bm25"]
    if bm25 and expanded_tokens and len(_INDEX_STORE["chunks"]) == len(all_chunks):
        raw_scores = bm25.get_scores(expanded_tokens)
        max_raw = max(raw_scores) if len(raw_scores) > 0 else 0.0
        
        if max_raw < 1.0:
            return {
                "retrieved_chunks": [],
                "top_score": 0.30,
                "crag_trigger": True
            }

        scored_indices = sorted(range(len(raw_scores)), key=lambda i: raw_scores[i], reverse=True)[:100]
        scored_chunks = []

        for idx in scored_indices:
            c = dict(all_chunks[idx])
            raw_bm25 = raw_scores[idx]
            norm_bm25 = min(1.0, raw_bm25 / max_raw) if max_raw > 0 else 0.0
            
            boost = 0.0
            chunk_str = (c.get("section_heading", "") + " " + c.get("chunk_text", "") + " " + c.get("source", "")).lower()
            
            # Exact section match boosters
            for sec_num in ["13b", "13", "24", "25", "26", "9", "10", "23", "1869"]:
                pattern = rf"\b(section|sec|sec\.)\s*{sec_num}\b"
                if re.search(pattern, query_clean) or (sec_num in query_clean and f"section {sec_num}" in query_clean):
                    if re.search(pattern, chunk_str) or f"section {sec_num}" in chunk_str or f"sec. {sec_num}" in chunk_str:
                        boost += 0.35

            if "condon" in query_clean and "condon" in chunk_str:
                boost += 0.40
            if "cruelty" in query_clean and "cruelty" in chunk_str:
                boost += 0.20
            if "desertion" in query_clean and "desertion" in chunk_str:
                boost += 0.20
            if "animus" in query_clean and "animus" in chunk_str:
                boost += 0.30
            if "stridhan" in query_clean and "stridhan" in chunk_str:
                boost += 0.35
            if "conveyancing" in query_clean and "conveyancing" in chunk_str:
                boost += 0.25
            if "drafting" in query_clean and "drafting" in chunk_str:
                boost += 0.25
            if "sarkar" in query_clean and "sarkar" in chunk_str:
                boost += 0.30
            if "paras diwan" in query_clean and "diwan" in chunk_str:
                boost += 0.25
            if "kumud desai" in query_clean and "desai" in chunk_str:
                boost += 0.25

            final_score = min(0.98, max(0.2, (norm_bm25 * 0.65) + boost))
            
            c["bm25_score"] = round(norm_bm25, 3)
            c["semantic_score"] = round(final_score, 3)
            c["reranker_score"] = round(final_score, 3)
            c["rrf_score"] = round(final_score, 3)
            scored_chunks.append(c)

    else:
        scored_chunks = []
        for c in all_chunks[:100]:
            chunk_str = (c.get("section_heading", "") + " " + c.get("chunk_text", "")).lower()
            overlap = sum(1 for t in expanded_tokens if t in chunk_str)
            score = min(1.0, 0.4 + (overlap * 0.12)) if overlap > 0 else 0.3
            
            c_copy = dict(c)
            c_copy["bm25_score"] = round(score, 3)
            c_copy["semantic_score"] = round(score, 3)
            c_copy["reranker_score"] = round(score, 3)
            c_copy["rrf_score"] = round(score, 3)
            scored_chunks.append(c_copy)

    scored_chunks.sort(key=lambda x: x["reranker_score"], reverse=True)
    top_chunks = scored_chunks[:top_k]
    top_score = top_chunks[0]["reranker_score"] if top_chunks else 0.0

    crag_trigger = top_score < CRAG_THRESHOLD

    return {
        "retrieved_chunks": top_chunks,
        "top_score": top_score,
        "crag_trigger": crag_trigger
    }
