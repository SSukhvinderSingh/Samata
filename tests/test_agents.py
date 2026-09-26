"""
Unit tests for Samata Agents module & Orchestrator.
"""

import pytest
from agents.qa_agent import run_qa_agent
from agents.simplifier import run_simplifier_agent
from agents.risk_spotter import run_risk_spotter_agent
from agents.comparator import run_comparator_agent
from agents.devils_advocate import run_devils_advocate_agent
from agents.orchestrator import orchestrate_query


def test_qa_agent():
    mock_context = [{
        "chunk_id": "c1",
        "chunk_text": "Section 13 of Hindu Marriage Act provides grounds for divorce including adultery, cruelty, and desertion.",
        "source": "HMA_1955.pdf",
        "section_heading": "Section 13 — Grounds for Divorce",
        "reranker_score": 0.85
    }]
    res = run_qa_agent("What are the grounds for divorce under Section 13?", mock_context, "test_session")
    assert "divorce" in res["answer"].lower() or "section 13" in res["answer"].lower()
    assert len(res["citations"]) >= 1


def test_simplifier_agent():
    res_en = run_simplifier_agent("Section 13 HMA clause text", "HMA 1955", "en")
    assert "In simple terms" in res_en["simplified_text"]

    res_hi = run_simplifier_agent("Section 13 HMA clause text", "HMA 1955", "hinglish")
    assert "Is rule" in res_hi["simplified_text"]


def test_risk_spotter_agent():
    doc_text = "Party A agrees to waive all claims to future alimony and maintenance under Section 25."
    res = run_risk_spotter_agent(doc_text)
    assert len(res["risk_flags"]) > 0
    assert res["risk_flags"][0]["severity"] == "High"


def test_comparator_agent():
    res = run_comparator_agent("Husband narrative text", "Wife narrative text", "narrative_vs_narrative")
    assert len(res["comparison_result"]) >= 3
    assert "summary" in res


def test_devils_advocate_agent():
    narrative = "My spouse left 6 months ago and I want to file for divorce on grounds of desertion and custody of my child."
    res = run_devils_advocate_agent(narrative)
    assert "synthesis" in res
    assert len(res["synthesis"]) > 0
    assert "disclaimer" in res
    assert res["resource_signpost"] != ""  # because child custody triggered sensitivity


def test_orchestrator():
    # Test Strategic Advocate routing
    res_da = orchestrate_query("Give me devil's advocate view on my divorce case", "orch_sess")
    assert "Strategic Advocate Agent" in res_da["agent_trace"]["agents_invoked"]

    # Test Q&A routing
    res_qa = orchestrate_query("What does Section 9 of Hindu Marriage Act cover?", "orch_sess")
    assert "Q&A Agent" in res_qa["agent_trace"]["agents_invoked"]


def test_orchestrator_greeting():
    res_greeting = orchestrate_query("hi", "orch_sess")
    assert "Conversational Welcome" in res_greeting["agent_trace"]["agents_invoked"]
    assert "Samata" in res_greeting["response"]
    assert "Disclaimer" in res_greeting["response"]


def test_orchestrator_agent_mentions():
    # Test @advocate
    res_adv = orchestrate_query("@advocate evaluate my separation narrative", "mention_sess")
    assert "Strategic Advocate Agent" in res_adv["agent_trace"]["agents_invoked"]
    assert "@devils_advocate mention" in res_adv["agent_trace"]["routing_reason"]

    # Test @risk
    res_risk = orchestrate_query("@risk Party A waives all rights to alimony", "mention_sess")
    assert "Risk Spotter Agent" in res_risk["agent_trace"]["agents_invoked"]

    # Test @simplify
    res_simp = orchestrate_query("@simplify Section 13(1)(ia)", "mention_sess")
    assert "Simplifier Agent" in res_simp["agent_trace"]["agents_invoked"]

    # Test @qa
    res_qa = orchestrate_query("@qa What is Section 24 HMA?", "mention_sess")
    assert "Q&A Agent" in res_qa["agent_trace"]["agents_invoked"]


def test_orchestrator_multi_agent_chaining():
    # Test multi-tagging @risk @advocate
    res_multi = orchestrate_query("@risk @advocate The draft deed states that I forfeit all custody rights upon signing.", "multi_sess")
    invoked = res_multi["agent_trace"]["agents_invoked"]
    assert "Risk Spotter Agent" in invoked
    assert "Strategic Advocate Agent" in invoked
    assert "Multi-Agent Deliberation Panel" in res_multi["agent_trace"]["routing_reason"]
    assert "Strategic Advocate Cross-Evaluation" in res_multi["response"]




