"""
Performance & Efficiency Benchmarks Unit Tests for Samata.
"""

import time
import pytest
from skills.sensitivity_classifier import classify_sensitivity
from skills.observability import redact_pii


def test_sensitivity_classifier_latency():
    """Ensure sensitivity classification executes under 50ms for rapid safety triage."""
    start = time.time()
    for _ in range(50):
        classify_sensitivity("What is the cooling-off period under Section 13B?")
    elapsed = time.time() - start
    avg_ms = (elapsed / 50) * 1000
    assert avg_ms < 50, f"Average latency {avg_ms:.2f}ms exceeds 50ms target"


def test_pii_redaction_throughput():
    """Ensure PII scrubbing performs at high throughput without latency degradation."""
    sample_text = "Contact party at john.doe@example.com or phone +91 9876543210 regarding mutual agreement."
    start = time.time()
    for _ in range(100):
        redact_pii(sample_text)
    elapsed = time.time() - start
    assert elapsed < 0.2, f"PII scrubbing batch took too long: {elapsed:.3f}s"
