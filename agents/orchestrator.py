"""
Orchestrator Agent for Samata Legal Assistant.
Central coordinator managing query classification, conversational greetings, agent routing, RAG retrieval, CRAG fallback, and response synthesis.
Supports explicit single and multi-agent @mentions (@advocate, @risk, @simplify, @compare, @qa), flexible conjunctions (&, and, commas), collaborative passage chaining, and clean citations.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from skills.rag_pipeline import retrieve_chunks
from skills.crag import execute_crag_fallback
from skills.sensitivity_classifier import classify_sensitivity
from skills.observability import log_trace
from skills.disclaimer import get_disclaimer
from skills.llm_client import call_llm

from agents.qa_agent import run_qa_agent
from agents.simplifier import run_simplifier_agent
from agents.risk_spotter import run_risk_spotter_agent
from agents.comparator import run_comparator_agent
from agents.devils_advocate import run_devils_advocate_agent


GREETING_SYSTEM_PROMPT = """You are Samata, a warm, empathetic, and knowledgeable Indian Matrimonial and Family Law Assistant.
The user is sending a greeting or introductory query.
Respond in a welcoming, empathetic, and professional tone.
Introduce yourself concisely and mention your key capabilities, including mentioning that they can tag specialist agents using @advocate, @risk, @simplify, @compare, or @qa:
1. Grounded Indian Family Law Q&A (@qa).
2. Strategic Multi-Lens Advocate (@advocate - evaluating spouse's arguments & judicial perspectives).
3. Separation Deed & Risk Spotting (@risk - checking draft clauses for hidden risks).
4. Plain English / Hinglish Simplification (@simplify).
Invite the user to share their question or narrative comfortably. Keep your greeting under 150 words.
"""


def parse_all_agent_mentions(user_message: str) -> Tuple[List[str], str]:
    """
    Parses all explicit @agent mentions in the prompt (e.g., '@advocate & @risk', '@risk @advocate').
    Returns (list_of_unique_agent_keys, cleaned_query).
    """
    msg = user_message.strip()
    found_agents = []

    # Check and extract agents preserving order
    patterns = [
        ("devils_advocate", r"@advocate\b|@devil\b|@counsel\b"),
        ("risk", r"@risk\b|@audit\b|@spotter\b"),
        ("simplify", r"@simplify\b|@explain\b|@plain\b"),
        ("compare", r"@compare\b|@diff\b|@versus\b"),
        ("qa", r"@qa\b|@ask\b|@research\b")
    ]

    for agent_key, pat in patterns:
        if re.search(pat, msg, flags=re.IGNORECASE):
            found_agents.append(agent_key)
            msg = re.sub(pat, "", msg, flags=re.IGNORECASE)

    # Clean up residual connecting punctuation like '&', 'and', commas at the start
    clean_msg = re.sub(r"^[\s,&+and]+", "", msg).strip()
    clean_msg = re.sub(r"\s+", " ", clean_msg).strip()

    return found_agents, clean_msg


def is_greeting_intent(query: str) -> bool:
    """
    Identifies casual greetings, pleasantries, or introductory small talk.
    """
    clean = query.lower().strip().rstrip("!.,?")
    words = clean.split()
    
    greeting_exact = {
        "hi", "hello", "hey", "namaste", "namaskar", "good morning", 
        "good afternoon", "good evening", "greetings", "help", 
        "who are you", "what can you do", "kya kar sakte ho", "intro", "start",
        "how are you", "what is samata", "test"
    }
    
    if clean in greeting_exact:
        return True
    
    if len(words) <= 3 and any(w in ["hi", "hello", "hey", "namaste", "namaskar"] for w in words):
        return True
        
    return False


def orchestrate_query(
    user_message: str,
    session_id: str = "default_session",
    document_text: Optional[str] = None,
    document_chunks: Optional[List[Dict[str, Any]]] = None,
    user_language_preference: str = "en",
    slm_model: Optional[str] = None,
    main_model: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Main entry point for Samata multi-agent system.
    Routes query via @mentions or intent heuristics, executes collaborative multi-agent deliberation when multiple tags are present,
    and returns conversational passage-style responses with citations strictly following the passage.
    """
    # 1. Parse all @mentions (e.g. '@advocate & @risk')
    tagged_agents, clean_message = parse_all_agent_mentions(user_message)
    # Keep full user_message if stripping tags left an empty string (user typed only tags)
    effective_message = clean_message.strip() if clean_message.strip() else user_message.strip()
    query_lower = effective_message.lower().strip()
    
    invoked_agents = []
    crag_triggered = False

    # 2. Sensitivity check
    sens_res = classify_sensitivity(effective_message)
    sensitivity_flags = sens_res["sensitivity_flags"]

    # 3. Greeting / Conversational check (only if no explicit @agent)
    if not tagged_agents and is_greeting_intent(effective_message):
        invoked_agents.append("Conversational Welcome")
        
        greeting_llm = call_llm(
            system_prompt=GREETING_SYSTEM_PROMPT,
            user_prompt=effective_message,
            model=main_model,
            temperature=0.4,
            max_tokens=300,
            chat_history=chat_history
        )
        
        if greeting_llm:
            final_narrative = greeting_llm
        else:
            final_narrative = (
                "Hello! I am **Samata**, your Indian Matrimonial & Family Law Assistant. ⚖️\n\n"
                "I'm here to help you navigate legal questions, evaluate conflict scenarios, and prepare for consultations under Indian Family Law (*Hindu Marriage Act 1955*, *Special Marriage Act 1954*, and *Divorce Act 1869*).\n\n"
                "### Specialist Handles:\n"
                "- 📖 `@qa` — **Statutory & Case Law Q&A**: Ask about maintenance/alimony (Sec 24/25), child custody (Sec 26), or divorce grounds.\n"
                "- ⚖️ `@advocate` — **Strategic Multi-Lens Advocate**: Explore your spouse's counter-arguments, evidentiary gaps, and judicial perspectives.\n"
                "- 🚩 `@risk` — **Separation Deed & Risk Spotting**: Spot one-sided terms or waiver traps.\n"
                "- 🗣️ `@simplify` — **Plain Language & Hinglish**: Translate complex legalese into clear practical terms.\n"
                "- 📊 `@compare` — **Comparator**: Compare narratives or clauses against standard baselines.\n\n"
                "*Tip: You can tag multiple specialists (e.g. `@risk @advocate`) for a collaborative cross-evaluation!*"
            )
            
        disclaimer = get_disclaimer("standard")
        full_response = f"{final_narrative}\n\n---\n> **Disclaimer**: {disclaimer}"
        
        agent_trace = {
            "agents_invoked": invoked_agents,
            "routing_reason": "Conversational Greeting & Capabilities Overview",
            "retrieval_score": 1.0,
            "crag_triggered": False,
            "token_usage": 150,
            "sensitivity_flags": sensitivity_flags,
            "slm_model_used": slm_model or "default_slm",
            "main_model_used": main_model or "default_llm",
            "slm_brief": ""
        }
        
        log_trace(
            session_id=session_id,
            agent_name="Orchestrator Agent",
            input_summary=user_message,
            routing_reason="Conversational Greeting Handler",
            retrieved_chunks=[],
            token_usage=150,
            crag_triggered=False,
            extra_metadata={}
        )
        
        return {
            "response": full_response,
            "agent_trace": agent_trace,
            "session_state": {"last_invoked": "Conversational Welcome", "session_id": session_id}
        }

    # 4. RAG Retrieval — base 13k legal corpus + any uploaded document chunks
    retrieval_query = effective_message
    if chat_history and len(effective_message.split()) <= 12:
        # Contextual follow-up query expansion using previous user query context
        prev_user_queries = [m.get("content", "") for m in chat_history if m.get("role") == "user"]
        if prev_user_queries:
            # Combine last turn context with the follow-up question for accurate statute retrieval
            retrieval_query = f"{prev_user_queries[-1]} {effective_message}"

    rag_res = retrieve_chunks(
        retrieval_query,
        top_k=5,
        document_context_chunks=document_chunks or None
    )
    retrieved_chunks = rag_res["retrieved_chunks"]
    top_score = rag_res["top_score"]

    if rag_res["crag_trigger"]:
        crag_triggered = True
        crag_res = execute_crag_fallback(retrieval_query, top_score)
        retrieved_chunks = crag_res["secondary_chunks"]
        top_score = crag_res["secondary_top_score"]

    # 5. MULTI-AGENT COLLABORATION HARNESS (When 2+ agents are tagged)
    if len(tagged_agents) > 1:
        collaborative_sections = []
        intermediate_context = ""

        # Run non-DA agents first so Strategic Advocate can cross-reference their findings
        AGENT_ORDER = ["qa", "risk", "simplify", "compare", "devils_advocate"]
        ordered_tags = sorted(tagged_agents, key=lambda t: AGENT_ORDER.index(t) if t in AGENT_ORDER else 99)

        for tag in ordered_tags:
            if tag == "risk":
                invoked_agents.append("Risk Spotter Agent")
                doc_input = document_text if document_text else effective_message
                risk_out = run_risk_spotter_agent(doc_input, retrieved_chunks, session_id)
                flags_str = "\n".join([f"- **[{f['severity']} Severity]**: {f['reason']}\n  *Relevant Term*: \"{f['clause_excerpt']}\"" for f in risk_out["risk_flags"]])
                collaborative_sections.append(
                    f"### 🚩 Risk Spotter Analysis\n\n"
                    f"In reviewing the terms and claims in your matter, the following legal and strategic risks require attention:\n\n"
                    f"{flags_str}"
                )
                intermediate_context += f"\n[Risk Spotter Identified Pitfalls]:\n{flags_str}\n"

            elif tag == "devils_advocate":
                invoked_agents.append("Strategic Advocate Agent")
                da_prompt = f"{effective_message}\n\n<collaborative_agent_context>\n{intermediate_context}\n</collaborative_agent_context>" if intermediate_context else effective_message
                da_out = run_devils_advocate_agent(
                    user_narrative=da_prompt,
                    rag_context=retrieved_chunks,
                    document_context=document_text,
                    session_id=session_id,
                    slm_model=slm_model,
                    main_model=main_model,
                    chat_history=chat_history
                )
                collaborative_sections.append(f"### ⚖️ Strategic Advocate Cross-Evaluation\n\n{da_out['synthesis']}")
                intermediate_context += f"\n[Strategic Advocate Evaluation]:\n{da_out['synthesis']}\n"

            elif tag == "simplify":
                invoked_agents.append("Simplifier Agent")
                simp_out = run_simplifier_agent(effective_message, "Hindu Marriage Act 1955", user_language_preference, session_id)
                collaborative_sections.append(f"### 🗣️ Plain-Language Breakdown\n\n{simp_out['simplified_text']}")

            elif tag == "compare":
                invoked_agents.append("Comparator Agent")
                comp_out = run_comparator_agent(effective_message, "Standard Legal Baseline Template", "draft_vs_template", session_id)
                diff_str = "\n".join([f"- **[{c['category']}]**: {c['significance']}\n  *Term*: \"{c['excerpt_a']}\"" for c in comp_out["comparison_result"]])
                collaborative_sections.append(f"### 📊 Comparative Analysis\n\n{comp_out['summary']}\n\n{diff_str}")

            elif tag == "qa":
                invoked_agents.append("Q&A Agent")
                qa_out = run_qa_agent(
                    user_question=effective_message,
                    rag_context=retrieved_chunks,
                    session_id=session_id,
                    document_context=document_text,
                    slm_model=slm_model,
                    main_model=main_model,
                    chat_history=chat_history
                )
                collaborative_sections.append(f"### 📖 Statutory Guidance\n\n{qa_out['answer']}")

        agent_names = " and ".join(invoked_agents)
        intro = f"*Your query has been reviewed by {agent_names} in a collaborative deliberation. Each specialist's assessment is presented below.*\n\n"
        final_narrative = intro + "\n\n---\n\n".join(collaborative_sections)
        disclaimer = get_disclaimer("standard")
        full_response = f"{final_narrative}\n\n---\n> **Disclaimer**: {disclaimer}"
        
        agent_trace = {
            "agents_invoked": invoked_agents,
            "routing_reason": f"Multi-Agent Deliberation Panel: {', '.join(['@' + t for t in tagged_agents])}",
            "retrieval_score": top_score,
            "crag_triggered": crag_triggered,
            "token_usage": 1500,
            "sensitivity_flags": sensitivity_flags,
            "slm_model_used": slm_model or "default_slm",
            "main_model_used": main_model or "default_llm",
            "slm_brief": intermediate_context
        }

        return {
            "response": full_response,
            "agent_trace": agent_trace,
            "session_state": {"last_invoked": ", ".join(invoked_agents), "session_id": session_id}
        }

    # 6. SINGLE AGENT EXECUTION
    single_tag = tagged_agents[0] if tagged_agents else None
    slm_brief = ""
    final_narrative = ""
    disclaimer = ""

    if single_tag == "devils_advocate" or (not single_tag and re.search(r"\b(stress[\s-]?test|devil'?s\s*advocate|opposing\s*counsel|opposing\s*lawyer|counter[\s-]?arguments?|cross[\s-]?examin\w*)\b", query_lower)):
        invoked_agents.append("Strategic Advocate Agent")
        da_out = run_devils_advocate_agent(
            user_narrative=effective_message,
            rag_context=retrieved_chunks,
            document_context=document_text,
            session_id=session_id,
            slm_model=slm_model,
            main_model=main_model,
            chat_history=chat_history
        )
        slm_brief = da_out.get("slm_brief", "")
        final_narrative = da_out["synthesis"]
        if da_out.get("resource_signpost"):
            final_narrative = f"> [!WARNING]\n> {da_out['resource_signpost']}\n\n" + final_narrative
        disclaimer = da_out["disclaimer"]

    elif single_tag == "simplify" or (not single_tag and re.search(r"\b(simplif\w*|plain\s*english|hinglish|easy\s*words?|explain\s*in\s*simple)\b", query_lower)):
        invoked_agents.append("Simplifier Agent")
        simp_out = run_simplifier_agent(effective_message, "Hindu Marriage Act 1955", user_language_preference, session_id)
        final_narrative = f"{simp_out['simplified_text']}"
        disclaimer = simp_out["disclaimer"]

    elif single_tag == "risk" or (not single_tag and re.search(r"\b(risk\s*spot\w*|red[\s-]?flags?|hidden\s*risks?|check\s*deed|check\s*agreement|waiver\s*trap)\b", query_lower)):
        invoked_agents.append("Risk Spotter Agent")
        doc_input = document_text if document_text else effective_message
        risk_out = run_risk_spotter_agent(doc_input, retrieved_chunks, session_id)
        flags_str = "\n".join([f"- **[{f['severity']} Severity]**: {f['reason']}\n  *Relevant Term*: \"{f['clause_excerpt']}\"" for f in risk_out["risk_flags"]])
        final_narrative = (
            f"### Separation & Agreement Risk Analysis\n\n"
            f"Upon reviewing your terms and narrative, the following legal risks and potential traps were identified:\n\n"
            f"{flags_str}\n\n"
            f"### Key Legal Provisions & References\n"
            f"- **Section 23(1)(c) — Bar on Collusion / Agreement Coercion**\n"
            f"- **Section 25 — Permanent Alimony & Maintenance Safeguards**"
        )
        disclaimer = risk_out["disclaimer"]

    elif single_tag == "compare" or (not single_tag and re.search(r"\b(compar\w*|diff\b|versus|vs\.?|difference\s*between)\b", query_lower)):
        invoked_agents.append("Comparator Agent")
        mode = "narrative_vs_narrative" if "party" in query_lower or "versus" in query_lower else "draft_vs_template"
        comp_out = run_comparator_agent(effective_message, "Standard Legal Baseline Template", mode, session_id)
        diff_str = "\n".join([f"- **[{c['category']}]**: {c['significance']}\n  *Term A*: \"{c['excerpt_a']}\"\n  *Term B*: \"{c['excerpt_b']}\"" for c in comp_out["comparison_result"]])
        final_narrative = f"### Legal Comparison Analysis ({mode})\n\n**{comp_out['summary']}**\n\n{diff_str}"
        disclaimer = comp_out["disclaimer"]

    else:  # Default Q&A
        invoked_agents.append("Q&A Agent")
        qa_out = run_qa_agent(
            user_question=effective_message,
            rag_context=retrieved_chunks,
            session_id=session_id,
            document_context=document_text,
            slm_model=slm_model,
            main_model=main_model,
            chat_history=chat_history
        )
        slm_brief = qa_out.get("slm_brief", "")
        final_narrative = qa_out["answer"]
        disclaimer = qa_out["disclaimer"]

    # Append clean non-dismissable disclaimer
    full_response = f"{final_narrative}\n\n---\n> **Disclaimer**: {disclaimer}"

    agent_name_str = invoked_agents[0] if invoked_agents else "Q&A Agent"
    routing_desc = f"@{single_tag} mention" if single_tag else f"Classified intent: {agent_name_str}"

    agent_trace = {
        "agents_invoked": invoked_agents,
        "routing_reason": routing_desc,
        "retrieval_score": top_score,
        "crag_triggered": crag_triggered,
        "token_usage": 1100,
        "sensitivity_flags": sensitivity_flags,
        "slm_model_used": slm_model or "default_slm",
        "main_model_used": main_model or "default_llm",
        "slm_brief": slm_brief
    }

    log_trace(
        session_id=session_id,
        agent_name="Orchestrator Agent",
        input_summary=effective_message,
        routing_reason=agent_trace["routing_reason"],
        retrieved_chunks=retrieved_chunks,
        token_usage=agent_trace["token_usage"],
        crag_triggered=crag_triggered,
        extra_metadata={"slm_brief": slm_brief}
    )

    return {
        "response": full_response,
        "agent_trace": agent_trace,
        "session_state": {"last_invoked": agent_name_str, "session_id": session_id}
    }
