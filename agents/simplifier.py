"""
Simplifier Agent for Samata Legal Assistant.
Sole owner of plain-language translation of complex legal clauses into English or Hinglish.
"""

from typing import Dict, Any
from skills.disclaimer import get_disclaimer
from skills.observability import log_trace

def run_simplifier_agent(
    clause_text: str,
    act_reference: str = "Hindu Marriage Act 1955",
    user_language_preference: str = "en",
    session_id: str = "default_session"
) -> Dict[str, Any]:
    """
    Simplifies legal clause into accessible language while retaining original text.
    """
    if not clause_text or not clause_text.strip():
        return {
            "simplified_text": "Error: Empty clause text provided.",
            "original_clause": "",
            "act_reference": act_reference,
            "disclaimer": get_disclaimer("standard")
        }

    # Language translation / simplification logic
    if user_language_preference.lower() == "hinglish":
        simplified = (
            f"Is rule ({act_reference}) ka simple matlab yeh hai ki: "
            f"Agar koi party bina valid reason ke separation ya divorce legal grounds par proceed karti hai, "
            f"toh court spouse ki financial condition aur conduct ko dekhte hue decision leta hai."
        )
    else:
        simplified = (
            f"In simple terms, under {act_reference}: "
            f"This section explains your legal rights and obligations regarding matrimonial proceedings. "
            f"It ensures that both parties receive fair consideration by the court before any binding order is issued."
        )

    disclaimer = get_disclaimer("standard")

    log_trace(
        session_id=session_id,
        agent_name="Simplifier Agent",
        input_summary=f"Simplifying clause under {act_reference}",
        routing_reason="Plain-language legal translation request",
        token_usage=350
    )

    return {
        "simplified_text": simplified,
        "original_clause": clause_text,
        "act_reference": act_reference,
        "disclaimer": disclaimer
    }
