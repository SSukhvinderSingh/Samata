"""
Sensitivity Classifier Skill for Samata Legal Assistant.
Detects emotional distress, crisis signals, domestic violence, and child custody flags.
"""

import re
from typing import Dict, List, Any

# Keyword and pattern mappings for sensitivity detection
PATTERNS = {
    "domestic_violence": [
        r"\bhits?\b", r"\bbeats?\b", r"\babuse[sd]?\b", r"\bphysical violence\b",
        r"\bdomestic violence\b", r"\b498a\b", r"\bassaulted\b", r"\bthreaten(ed|s)?\b",
        r"\bviolence\b", r"\bbruise[s]?\b", r"\bharm(ed)? me\b"
    ],
    "child_custody": [
        r"\bcustody\b", r"\bchild(ren)?\b", r"\bkid[s]?\b", r"\bvisitation\b",
        r"\bguardianship\b", r"\bminor child\b", r"\bsupervised access\b"
    ],
    "mental_health": [
        r"\bsuicide\b", r"\bkill myself\b", r"\bend my life\b", r"\bhopeless\b",
        r"\bcannot live\b", r"\bdepressed\b", r"\bself-harm\b", r"\bdistress\b"
    ],
    "financial_coercion": [
        r"\bdowry\b", r"\bextort(ion)?\b", r"\bseized my money\b", r"\bstridhan\b",
        r"\bwithheld funds\b", r"\bstarving\b"
    ]
}

HELPLINES = {
    "iCall": "9152987821",
    "SNEHI": "011-65978181",
    "National Domestic Violence Helpline": "181"
}


def classify_sensitivity(user_text: str) -> Dict[str, Any]:
    """
    Scans user text for sensitive topics and emergency signals.
    """
    if not user_text:
        return {"sensitivity_flags": [], "escalate_immediately": False, "helplines": {}}

    flags = []
    escalate_immediately = False
    text_lower = user_text.lower()

    for category, pattern_list in PATTERNS.items():
        for pattern in pattern_list:
            if re.search(pattern, text_lower):
                if category not in flags:
                    flags.append(category)
                if category in ["domestic_violence", "mental_health"]:
                    escalate_immediately = True
                break

    helpline_info = HELPLINES if escalate_immediately or "child_custody" in flags else {}

    return {
        "sensitivity_flags": flags,
        "escalate_immediately": escalate_immediately,
        "helplines": helpline_info
    }
