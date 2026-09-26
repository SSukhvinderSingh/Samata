"""
Risk Classification Skill for Samata Legal Assistant.
Defines static severity taxonomy and classification logic for legal document clauses.
"""

import re
from typing import Dict, Any

TAXONOMY_VERSION = "1.0.0"

HIGH_RISK_PATTERNS = [
    r"waive.*maintenance", r"waive.*alimony", r"forfeit.*maintenance", r"relinquish.*maintenance",
    r"waive.*custody", r"forfeit.*custody", r"no right to custody", r"waive.*property",
    r"no right to divorce", r"waive.*divorce", r"forfeit.*alimony", r"no claim to alimony",
    r"no future claims", r"bar from seeking legal recourse", r"waive.*statutory rights",
    r"waive.*claim"
]

MEDIUM_RISK_PATTERNS = [
    r"asymmetric", r"sole discretion", r"unilateral decision", r"non-standard division",
    r"one-sided arbitration", r"indemnify spouse", r"confidentiality penalty", r"strict penalty",
    r"no modification allowed"
]


def classify_clause_risk(clause_text: str, act_scope: str = "both") -> Dict[str, Any]:
    """
    Classifies legal clause severity based on standard HMA/SMA risk taxonomy.
    """
    text_lower = clause_text.lower()
    
    # High severity check
    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "severity": "High",
                "reason": f"Clause contains waiver of statutory right or core protection (pattern matched: '{pattern}').",
                "reference": "HMA Section 25 / SMA Section 37 (Statutory Rights)",
                "taxonomy_version": TAXONOMY_VERSION
            }
            
    # Medium severity check
    for pattern in MEDIUM_RISK_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                "severity": "Medium",
                "reason": f"Clause includes non-standard or asymmetrical financial/procedural obligation (pattern matched: '{pattern}').",
                "reference": "Standard Matrimonial Agreement Guidelines",
                "taxonomy_version": TAXONOMY_VERSION
            }

    # Low severity default
    return {
        "severity": "Low",
        "reason": "Clause deviates slightly from standard phrasing but preserves statutory rights.",
        "reference": "General Legal Drafting Standard",
        "taxonomy_version": TAXONOMY_VERSION
    }
