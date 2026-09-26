"""
Feedback Collector Skill for Samata Legal Assistant.
Logs thumbs up/down ratings and user feedback for retrieval and agent quality monitoring.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

from skills.observability import redact_pii

FEEDBACK_FILE = Path("feedback_log.jsonl")
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit

def log_feedback(
    session_id: str,
    agent_name: str,
    response_id: str,
    rating: str,  # 'thumbs_up' | 'thumbs_down'
    comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Appends a feedback entry to feedback_log.jsonl.
    """
    if rating not in ["thumbs_up", "thumbs_down"]:
        return {"logged": False, "error": "Invalid rating type. Must be 'thumbs_up' or 'thumbs_down'."}

    if FEEDBACK_FILE.exists() and FEEDBACK_FILE.stat().st_size > MAX_FILE_SIZE_BYTES:
        return {"logged": False, "error": "Feedback store exceeded maximum size (50MB)."}

    # Anonymize session_id
    anon_session_id = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]
    
    clean_comment = redact_pii(comment) if comment else None
    if clean_comment and len(clean_comment) > 200:
        clean_comment = clean_comment[:200]

    feedback_id = f"fb_{int(time.time() * 1000)}"

    entry = {
        "feedback_id": feedback_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id_hash": anon_session_id,
        "agent_name": agent_name,
        "response_id": response_id,
        "rating": rating,
        "comment": clean_comment,
        "flagged_for_review": (rating == "thumbs_down" and bool(clean_comment))
    }

    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return {"logged": True, "feedback_id": feedback_id}
