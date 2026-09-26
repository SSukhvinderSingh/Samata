"""
Risk Spotter Agent for Samata Legal Assistant.
Sole owner of identifying and flagging high-risk clauses and red flags in legal documents.
"""

from typing import Dict, List, Any
from skills.risk_classification import classify_clause_risk
from skills.disclaimer import get_disclaimer
from skills.observability import log_trace

def run_risk_spotter_agent(
    document_text: str,
    rag_context: List[Dict[str, Any]] = None,
    session_id: str = "default_session"
) -> Dict[str, Any]:
    """
    Scans document text for risky clauses and assigns severity flags.
    """
    if not document_text or not document_text.strip():
        return {
            "risk_flags": [],
            "disclaimer": get_disclaimer("document")
        }

    # Split document into paragraphs/clauses for evaluation
    paragraphs = [p.strip() for p in document_text.split("\n") if p.strip()]
    risk_flags = []

    for idx, para in enumerate(paragraphs):
        classification = classify_clause_risk(para)
        # Include if flagged High or Medium, or if single short doc
        if classification["severity"] in ["High", "Medium"] or len(paragraphs) == 1:
            risk_flags.append({
                "clause_excerpt": para[:150] + ("..." if len(para) > 150 else ""),
                "severity": classification["severity"],
                "reason": classification["reason"],
                "reference": classification["reference"]
            })

    # Fallback if no high/medium risks found
    if not risk_flags and paragraphs:
        risk_flags.append({
            "clause_excerpt": paragraphs[0][:150],
            "severity": "Low",
            "reason": "No high-risk statutory waivers detected in uploaded text.",
            "reference": "Standard Matrimonial Compliance Check"
        })

    disclaimer = get_disclaimer("document")

    log_trace(
        session_id=session_id,
        agent_name="Risk Spotter Agent",
        input_summary="Document clause risk spotter scan",
        routing_reason="Document risk analysis request",
        token_usage=600
    )

    return {
        "risk_flags": risk_flags,
        "disclaimer": disclaimer
    }
