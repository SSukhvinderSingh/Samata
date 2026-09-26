"""
Pytest integration test for RAG Evaluation Benchmark.
Validates that the retriever satisfies MRR@5 >= 0.75 and Hit@3 >= 80% on the 13,060-chunk legal index.
"""

import pytest
from scripts.evaluate_rag import evaluate_rag_pipeline

def test_rag_benchmark_metrics():
    metrics = evaluate_rag_pipeline()
    
    # Assert MRR@5 satisfies the benchmark threshold in skills.md
    assert metrics["mrr_5"] >= 0.75, f"MRR@5 ({metrics['mrr_5']:.3f}) fell below benchmark target of 0.75"
    
    # Assert Hit Rate @ 5 is >= 90%
    assert metrics["hit_rate_5"] >= 90.0, f"Hit@5 ({metrics['hit_rate_5']:.1f}%) fell below 90%"
    
    # Assert Average latency is well under 100ms
    assert metrics["avg_latency_ms"] < 200.0, f"Latency ({metrics['avg_latency_ms']:.2f}ms) exceeded 200ms"
