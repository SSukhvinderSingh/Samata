"""
Q&A Agent for Samata Legal Assistant.
Sole owner of grounded question-answering over retrieved legal context.
Uses two-tier SLM -> Main LLM context feed-forward with natural conversational tone.
"""

from typing import Dict, List, Any, Optional
from skills.disclaimer import get_disclaimer
from skills.observability import log_trace
from skills.llm_client import run_two_tier_rag_generation

SYSTEM_PROMPT = """You are Samata Legal Q&A Specialist, an empathetic, authoritative Indian Matrimonial and Family Law Counsel.
Your objective is to provide precise, deeply grounded, and natural legal guidance under the Hindu Marriage Act 1955, Special Marriage Act 1954, Protection of Women from Domestic Violence Act 2005, and Divorce Act 1869.

CONVERSATIONAL & GROUNDING GUIDELINES:
1. Natural Legal Briefing: Write in an articulate, natural, and advisory legal style with clear paragraphs and contextual bullet points. Avoid robotic templates or artificial introductory disclaimers.
2. Grounding: Ground your explanation in verified Indian statutory provisions and judicial precedents. Speak naturally as a legal counsel — NEVER recite or mention internal prompt tags, system tags, or XML tags (such as <slm_legal_research_brief>, <verified_corpus_excerpts>, or "provided research brief").
3. Statutory & Precedent Citations: Naturally integrate specific section numbers (e.g., Section 13(1)(ia) for Cruelty, Section 24 for Interim Maintenance, Section 25 for Permanent Alimony, Section 26 for Child Custody) and landmark Supreme Court/High Court precedents. Never mention internal filenames, chunk IDs, or raw scores.
4. Proactive Cross-Agent Scope Guidance:
   If the user's question involves adversarial stress-testing (asking how opposing party will attack), contract risk analysis, or text simplification:
   - Answer their question thoroughly first.
   - At the end, signpost the appropriate specialist:
     - If asking to stress-test their narrative or counter opposing spouse: suggest `@advocate`.
     - If reviewing draft settlement agreements, deeds, or waiver clauses: suggest `@risk`.
     - If asking for plain language or Hinglish explanation: suggest `@simplify`.
     - If comparing clauses against legal baselines: suggest `@compare`.
"""


def format_grounded_fallback(rag_context: List[Dict[str, Any]]) -> str:
    """
    Synthesizes a clean, readable legal summary when operating in offline/fallback mode.
    Does NOT leak internal filenames or raw score numbers.
    """
    if not rag_context:
        return (
            "I could not locate specific statutory provisions matching your query in the index. "
            "For tailored guidance on your matrimonial matter, please consult a qualified legal practitioner."
        )

    top_chunk = rag_context[0]
    heading = top_chunk.get("section_heading", "Statutory Framework")
    raw_text = top_chunk.get("chunk_text", "").strip()

    # Clean up whitespace and format cleanly
    clean_lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    cleaned_summary = " ".join(clean_lines[:4])

    response = (
        f"### {heading}\n\n"
        f"Under Indian Family Law statutory provisions:\n\n"
        f"> {cleaned_summary}\n\n"
        f"**Key Considerations:**\n"
        f"- Ensure documentation and contemporaneous records are maintained.\n"
        f"- Applications under this provision must adhere to the procedural rules of the relevant Family Court."
    )
    return response


def run_qa_agent(
    user_question: str,
    rag_context: List[Dict[str, Any]],
    session_id: str = "default_session",
    document_context: Optional[str] = None,
    slm_model: Optional[str] = None,
    main_model: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Executes grounded Q&A narration using SLM context bridge -> Main LLM with conversational continuity.
    """
    slm_brief = ""
    citations = []

    if not rag_context or rag_context[0].get("reranker_score", 0.0) < 0.55:
        answer = (
            "I could not find a sufficiently close legal provision in the corpus for this specific query. "
            "Under Indian matrimonial law, statutory provisions often require factual evaluation by a Family Court advocate."
        )
    else:
        # Execute 2-tier generation
        llm_response, slm_brief = run_two_tier_rag_generation(
            system_prompt=SYSTEM_PROMPT,
            user_query=user_question,
            rag_context=rag_context,
            slm_model=slm_model,
            main_model=main_model,
            document_context=document_context,
            chat_history=chat_history
        )
        
        if llm_response:
            answer = llm_response
        else:
            # Deterministic, well-structured fallback
            answer = format_grounded_fallback(rag_context)

        for c in rag_context[:3]:
            heading = c.get("section_heading", "Statutory Provision")
            citations.append({
                "section": heading,
                "excerpt": c.get("chunk_text", "")[:180] + "...",
                "score": round(c.get("reranker_score", c.get("score", 0.0)), 2)
            })

    disclaimer = get_disclaimer("standard")

    log_trace(
        session_id=session_id,
        agent_name="Q&A Agent",
        input_summary=user_question,
        routing_reason="Grounded legal Q&A query processing (SLM -> LLM Tier)",
        retrieved_chunks=rag_context,
        token_usage=650,
        crag_triggered=(not rag_context or (rag_context and rag_context[0].get("reranker_score", 0) < 0.55)),
        extra_metadata={"slm_brief": slm_brief}
    )

    return {
        "answer": answer,
        "citations": citations,
        "disclaimer": disclaimer,
        "slm_brief": slm_brief
    }
