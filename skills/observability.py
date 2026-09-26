"""
Observability Skill for Samata Legal Assistant.
Logs per-turn agent traces for audit and the Streamlit UI reasoning panel.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

SESSIONS_DIR = Path("sessions")

def redact_pii(text: str) -> str:
    """Redacts common PII patterns (Aadhaar, phone numbers, email addresses) from text."""
    if not text:
        return text
    # Phone numbers (10 digits, optional country code)
    text = re.sub(r'(\+91[\-\s]?)?[6-9]\d{9}', '[REDACTED_PHONE]', text)
    # Aadhaar number (12 digits)
    text = re.sub(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', '[REDACTED_AADHAAR]', text)
    # Emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', text)
    return text

def log_trace(
    session_id: str,
    agent_name: str,
    input_summary: str,
    routing_reason: str,
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    token_usage: int = 0,
    crag_triggered: bool = False,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Logs an agent execution step to the session trace log file.
    """
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    trace_file = SESSIONS_DIR / f"session_{session_id}.json"
    
    clean_input = redact_pii(input_summary)
    clean_reason = redact_pii(routing_reason)
    
    clean_chunks = []
    if retrieved_chunks:
        for chunk in retrieved_chunks:
            clean_chunks.append({
                "chunk_id": chunk.get("chunk_id", "unknown"),
                "source": chunk.get("source", "unknown"),
                "reranker_score": chunk.get("reranker_score", chunk.get("score", 0.0)),
                "snippet": redact_pii(chunk.get("chunk_text", "")[:150])
            })

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
        "agent_name": agent_name,
        "input_summary": clean_input,
        "routing_reason": clean_reason,
        "retrieved_chunks": clean_chunks,
        "token_usage": token_usage,
        "crag_triggered": crag_triggered,
        "metadata": extra_metadata or {}
    }

    traces = get_session_traces(session_id)
    traces.append(entry)
    
    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(traces, f, indent=2)

    return {"trace_written": True, "trace_file_path": str(trace_file)}

def get_session_traces(session_id: str) -> List[Dict[str, Any]]:
    """Returns all logged trace entries for a given session."""
    trace_file = SESSIONS_DIR / f"session_{session_id}.json"
    if not trace_file.exists():
        return []
    try:
        with open(trace_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def clear_session_trace(session_id: str) -> bool:
    """Removes trace file for a session when session ends."""
    trace_file = SESSIONS_DIR / f"session_{session_id}.json"
    if trace_file.exists():
        os.remove(trace_file)
        return True
    return False
