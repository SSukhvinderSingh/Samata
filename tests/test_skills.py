"""
Unit tests for Samata Skills module.
"""

import os
import pytest
from skills.disclaimer import get_disclaimer, STANDARD_DISCLAIMER, DOCUMENT_DISCLAIMER, SENSITIVITY_DISCLAIMER
from skills.observability import log_trace, get_session_traces, redact_pii
from skills.feedback_collector import log_feedback
from skills.risk_classification import classify_clause_risk
from skills.sensitivity_classifier import classify_sensitivity
from skills.document_ingestion import parse_file
from skills.rag_pipeline import retrieve_chunks, load_or_build_index
from skills.crag import execute_crag_fallback


def test_disclaimer_skill():
    std = get_disclaimer("standard")
    assert STANDARD_DISCLAIMER in std

    doc = get_disclaimer("document")
    assert DOCUMENT_DISCLAIMER in doc

    sens = get_disclaimer("sensitivity")
    assert SENSITIVITY_DISCLAIMER in sens


def test_observability_pii_redaction():
    text = "Contact Shawn at +919876543210 or shawn@example.com with Aadhaar 1234-5678-9012."
    clean = redact_pii(text)
    assert "[REDACTED_PHONE]" in clean
    assert "[REDACTED_EMAIL]" in clean
    assert "[REDACTED_AADHAAR]" in clean


def test_observability_logging():
    res = log_trace(
        session_id="test_sess_123",
        agent_name="TestAgent",
        input_summary="Test Query",
        routing_reason="Testing"
    )
    assert res["trace_written"] is True
    traces = get_session_traces("test_sess_123")
    assert len(traces) >= 1
    assert traces[-1]["agent_name"] == "TestAgent"


def test_feedback_collector():
    fb_res = log_feedback("sess_456", "Q&A Agent", "resp_1", "thumbs_up", "Great response!")
    assert fb_res["logged"] is True


def test_risk_classification():
    res_high = classify_clause_risk("Wife hereby agrees to waive maintenance rights under HMA Section 25.")
    assert res_high["severity"] == "High"

    res_med = classify_clause_risk("Husband retains sole discretion over asset division.")
    assert res_med["severity"] == "Medium"

    res_low = classify_clause_risk("Both parties agree to reside separately.")
    assert res_low["severity"] == "Low"


def test_sensitivity_classifier():
    res_dv = classify_sensitivity("He hits me and abuses me physically.")
    assert "domestic_violence" in res_dv["sensitivity_flags"]
    assert res_dv["escalate_immediately"] is True

    res_cust = classify_sensitivity("I want custody of my minor child.")
    assert "child_custody" in res_cust["sensitivity_flags"]


def test_rag_pipeline_and_crag():
    load_or_build_index()
    res = retrieve_chunks("Section 13 grounds for divorce Hindu Marriage Act")
    assert len(res["retrieved_chunks"]) > 0
    assert res["top_score"] >= 0.55

    crag_res = execute_crag_fallback("unclear query", 0.40)
    assert crag_res["crag_status"] in ["resolved", "unresolved"]


def test_security_sanitization():
    from skills.llm_client import sanitize_legal_narrative
    raw_prompt_tags = "Here is the brief: <slm_legal_research_brief>Section 13</slm_legal_research_brief> <verified_corpus_excerpts>HMA_1955.pdf</verified_corpus_excerpts>"
    sanitized = sanitize_legal_narrative(raw_prompt_tags)
    assert "<slm_legal_research_brief>" not in sanitized
    assert "<verified_corpus_excerpts>" not in sanitized
    assert "HMA_1955.pdf" not in sanitized
    assert "Hindu Marriage Act, 1955" in sanitized

