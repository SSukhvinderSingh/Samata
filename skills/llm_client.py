"""
LLM & SLM Client Skill for Samata Legal Assistant.
Supports two-tier (SLM Context Bridge -> Main Reasoning LLM) generation via OpenRouter API.
Uses zero-dependency standard library HTTP client (urllib) with optional OpenAI SDK support.
Allows dynamic model selection during runtime and testing.
"""

import os
import json
import urllib.request
import urllib.error
import re
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv(override=True)

DEFAULT_SLM_MODEL = os.getenv("OPENROUTER_SLM_MODEL", "meta-llama/llama-3.2-3b-instruct")
DEFAULT_MAIN_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


SOURCE_CLEAN_MAP = {
    "sc_judgements_familymatters.pdf": "Supreme Court of India Precedents",
    "hma_1955.pdf": "Hindu Marriage Act, 1955",
    "divorce_act_1869.pdf": "Divorce Act, 1869",
    "paras_diwan.pdf": "Modern Hindu Law (Dr. Paras Diwan)",
    "kumud_desai.pdf": "Indian Law of Marriage & Divorce (Kumud Desai)",
    "sarkar.pdf": "Law of Maintenance (Sarkar)",
    "drafting_pleadings_conveyancing.pdf": "Pleadings & Matrimonial Conveyancing",
}


def clean_source_name(raw_source: str) -> str:
    """Converts internal filenames into authoritative legal treatise/statutory titles."""
    if not raw_source:
        return "Indian Family Law Statutory Authority"
    cleaned = raw_source.lower().strip()
    return SOURCE_CLEAN_MAP.get(cleaned, raw_source.replace(".pdf", "").replace(".docx", "").replace("_", " "))


def sanitize_legal_narrative(text: str) -> str:
    """
    Strict post-processing sanitizer: eliminates any accidental raw filenames (.pdf),
    'Source X:' numbers, 'Mode A/B/C' section headers, or raw index identifiers from LLM outputs.
    """
    if not text:
        return ""
    # Remove file extensions like .pdf, .docx
    text = re.sub(r"\b([A-Za-z0-9_]+)\.(pdf|docx|txt)\b", r"\1", text, flags=re.IGNORECASE)
    # Replace internal file identifier stems with clean legal authorities
    text = re.sub(r"SC_Judgements_FamilyMatters", "Supreme Court of India Precedents", text, flags=re.IGNORECASE)
    text = re.sub(r"HMA_1955", "Hindu Marriage Act, 1955", text, flags=re.IGNORECASE)
    text = re.sub(r"Divorce_Act_1869", "Divorce Act, 1869", text, flags=re.IGNORECASE)
    text = re.sub(r"Paras_Diwan", "Modern Hindu Law (Dr. Paras Diwan)", text, flags=re.IGNORECASE)
    text = re.sub(r"Kumud_Desai", "Indian Law of Marriage & Divorce (Kumud Desai)", text, flags=re.IGNORECASE)
    text = re.sub(r"\bSarkar\b", "Law of Maintenance (Sarkar)", text, flags=re.IGNORECASE)
    text = re.sub(r"Drafting_Pleadings_Conveyancing", "Legal Pleadings & Conveyancing", text, flags=re.IGNORECASE)
    # Remove raw 'Source 1:', 'Source 3:', etc.
    text = re.sub(r"\bSource\s+\d+:\s*", "", text, flags=re.IGNORECASE)
    # Strip "Mode A —", "Mode B —", "Mode C —" headers (with or without em dash variants)
    text = re.sub(
        r"#+\s*Mode\s+[A-Ca-c][\s\u2013\u2014\-]*[^\n]*\n?",
        "",
        text,
        flags=re.IGNORECASE
    )
    # Strip internal prompt XML tags (e.g. <slm_legal_research_brief>, <verified_corpus_excerpts>, etc.)
    text = re.sub(r"</?(?:slm_legal_research_brief|verified_corpus_excerpts|retrieved_legal_context|uploaded_document_context|collaborative_agent_context|raw_legal_corpus_chunks)>", "", text, flags=re.IGNORECASE)
    # Clean phrases like "Based on the provided <slm_legal_research_brief> and <verified_corpus_excerpts>," or "Based on the provided research brief,"
    text = re.sub(r"\bBased\s+on\s+the\s+provided\s+(?:and\s+)?(?:research\s+brief|excerpts|context|corpus|brief)?\s*,?\s*", "Based on Indian legal principles and statutory provisions, ", text, flags=re.IGNORECASE)
    # Collapse resulting double-blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()



def format_rag_context(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved chunks into clean, dignified legal authority references.
    Excludes all raw filenames, .pdf extensions, and numerical score values.
    """
    if not retrieved_chunks:
        return "No relevant legal provisions retrieved."

    formatted = []
    for c in retrieved_chunks:
        source = clean_source_name(c.get("source", "Indian Family Law Statutory Authority"))
        heading = c.get("section_heading", "Statutory Provision")
        text = c.get("chunk_text", "").strip()
        
        formatted.append(f"[Legal Authority: {heading} — {source}]\n{text}")

    return "\n\n".join(formatted)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 1500,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Calls OpenRouter LLM/SLM using zero-dependency urllib HTTP client.
    Supports chat history for natural multi-turn conversations.
    """
    load_dotenv(override=True)
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    target_model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_MAIN_MODEL)

    if not api_key or "mock" in api_key.lower() or "your_" in api_key.lower() or api_key == "test_key":
        return ""

    # Build messages payload with conversation history
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    
    if chat_history:
        # Include last 4 relevant turns for context
        for msg in chat_history[-4:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"] and content:
                # Strip disclaimer from assistant context to avoid prompt bloat
                clean_content = content.split("\n\n---\n> **Disclaimer**:")[0].strip()
                messages.append({"role": role, "content": clean_content})

    messages.append({"role": "user", "content": user_prompt})

    endpoint = f"{OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://samata.legal",
        "X-Title": "Samata Matrimonial Legal Assistant",
        "User-Agent": "Samata-Legal-Assistant/1.0"
    }

    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=45) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
            return ""
    except urllib.error.HTTPError as http_err:
        err_msg = ""
        try:
            err_msg = http_err.read().decode("utf-8")
        except Exception:
            pass
        print(f"Warning: OpenRouter HTTP {http_err.code} for model '{target_model}': {err_msg}. Falling back.")
        return ""
    except Exception as e:
        print(f"Warning: OpenRouter API call to '{target_model}' failed ({e}). Falling back.")
        return ""


def call_slm_briefing(
    user_query: str,
    retrieved_chunks: List[Dict[str, Any]],
    slm_model: Optional[str] = None
) -> str:
    """
    Tier 1 (SLM): Rapidly processes raw RAG chunks into a focused Legal Case Brief.
    """
    if not retrieved_chunks:
        return ""

    target_slm = slm_model or os.getenv("OPENROUTER_SLM_MODEL", DEFAULT_SLM_MODEL)
    context_str = format_rag_context(retrieved_chunks)

    slm_system_prompt = (
        "You are an expert Legal Research Associate SLM for Indian Matrimonial Law. "
        "Analyze the raw retrieved legal text and produce a concise, structured Legal Research Brief. "
        "Extract: (1) Applicable statutory provisions & sections, "
        "(2) Core judicial principles / precedents cited in the text, (3) Key evidentiary tests or statutory bars. "
        "Be factual, precise, and concise."
    )

    slm_user_prompt = (
        f"User Legal Query: {user_query}\n\n"
        f"<raw_legal_corpus_chunks>\n{context_str}\n</raw_legal_corpus_chunks>\n\n"
        f"Generate structured Legal Research Brief:"
    )

    return call_llm(slm_system_prompt, slm_user_prompt, model=target_slm, temperature=0.1, max_tokens=800)


def run_two_tier_rag_generation(
    system_prompt: str,
    user_query: str,
    rag_context: List[Dict[str, Any]],
    slm_model: Optional[str] = None,
    main_model: Optional[str] = None,
    document_context: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, str]:
    """
    Executes the 2-Tier Architecture:
    1. SLM reads raw RAG chunks and creates a structured Legal Brief.
    2. Main Reasoning LLM takes the SLM Brief + User Query + Raw Excerpts + Chat History to formulate final analysis.
    Returns (final_response_text, slm_brief_text).
    """
    # 1. Tier 1: SLM generates structured legal brief
    slm_brief = call_slm_briefing(user_query, rag_context, slm_model=slm_model)

    # 2. Tier 2: Build Main Model Prompt
    raw_context_str = format_rag_context(rag_context)
    doc_info = f"\n<uploaded_document_context>\n{document_context}\n</uploaded_document_context>" if document_context else ""
    
    if slm_brief:
        combined_context = (
            f"<slm_legal_research_brief>\n{slm_brief}\n</slm_legal_research_brief>\n\n"
            f"<verified_corpus_excerpts>\n{raw_context_str}\n</verified_corpus_excerpts>"
        )
    else:
        combined_context = f"<retrieved_legal_context>\n{raw_context_str}\n</retrieved_legal_context>"

    main_user_prompt = f"{combined_context}{doc_info}\n\nUser Question/Narrative:\n{user_query}"

    final_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=main_user_prompt,
        model=main_model,
        temperature=0.25,
        max_tokens=2000,
        chat_history=chat_history
    )

    clean_final_response = sanitize_legal_narrative(final_response)

    return clean_final_response, slm_brief
