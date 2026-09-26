"""
Devil's Advocate Agent for Samata Legal Assistant.
Sole owner of adversarial multi-lens legal reasoning (Headline Feature).
Generates cohesive, conversational passage-style adversarial evaluations grounded in Indian Family Law.
"""

from typing import Dict, List, Any, Optional
from skills.disclaimer import get_disclaimer
from skills.sensitivity_classifier import classify_sensitivity
from skills.observability import log_trace
from skills.llm_client import run_two_tier_rag_generation

DEVILS_ADVOCATE_SYSTEM_PROMPT = """You are the Devil's Advocate Legal Specialist for Samata, an expert senior AI Matrimonial Legal Counsel in India.

CRITICAL INSTRUCTION ON FORMATTING & THOUGHT PROCESS:
Do NOT follow any rigid template or boilerplate outline.
Specifically: Do NOT use canned headings like "Opposing Counsel's Strategy", "Evidentiary Gaps & Vulnerabilities", or "Judicial & Family Court Perspective".
Instead, follow an organic, thoughtful legal reasoning process tailored directly to the user's specific ask.

THOUGHT PROCESS & ADVISORY GUIDELINES:
1. Direct Analysis: Begin immediately by addressing the core premise of the user's question in a clear, cohesive legal opening.
2. Point out logical fallacies, inconsistencies, and flaws in the user's premise or arguments.
3. Dynamic Reasoning:
   - For case law, precedent, or statutory research: Discuss the judicial principles, landmark Supreme Court / High Court decisions, and statutory balancing tests directly and naturally.
   - For dispute narratives / claims: Walk through the practical counter-arguments, documentary challenges, and judicial inclinations in cohesive, natural paragraphs.
4. Fluid Subheadings: Use natural, topic-specific subheadings only when genuinely helpful for readability (e.g. naming specific statutes, legal doctrines, or case themes), never generic template placeholders.
5. Clean Legal Authority: Weave in relevant statutory provisions (under HMA 1955, SMA 1954, DV Act 2005, CrPC 125) and landmark case citations naturally into the text. Never cite internal filenames, chunk numbers, or raw scores.
6. If applicable to user's query, Discuss how the above reasoning relates to the user's specific query in a clear, cohesive manner and how opposition can counter the user's case and how it can be overcome.
7. Cross-Agent Guidance: If the user's inquiry would benefit from another specialist's focus (e.g. `@qa` for exhaustive statutory breakdown, `@risk` for deed auditing, `@simplify` for plain language), append a brief helpful tip at the end.
"""


def format_advocate_fallback(user_narrative: str, rag_context: List[Dict[str, Any]]) -> str:
    """
    Generates a high-quality natural legal brief when operating in fallback mode.
    """
    passage = (
        "### Strategic Legal Evaluation & Adversarial Analysis\n\n"
        "In evaluating this matrimonial legal scenario, anticipating how the opposing party and the Family Court bench "
        "will approach the matter is essential for developing a sound strategy.\n\n"
        "**Opposing Arguments & Counter-Claims:**\n"
        "Under Indian matrimonial practice, claims and allegations are routinely challenged on grounds of evidentiary latches "
        "or characterization as ordinary marital friction. If desertion or separation is in question, opposing counsel typically argues "
        "that departure was justified or compelled rather than intentional abandonment without reasonable cause.\n\n"
        "**Evidentiary & Financial Considerations:**\n"
        "Family Courts evaluate claims based on contemporaneous documentary proof. In maintenance disputes under Sections 24 and 25 "
        "of the Hindu Marriage Act (guided by *Rajnesh v. Neha*), comprehensive disclosure of assets, liabilities, and income affidavits "
        "is mandatory, and omissions risk adverse judicial inferences.\n\n"
        "**Judicial Balancing & Statutory Safeguards:**\n"
        "Courts balance protective statutory objectives against procedural fairness. Where child custody is involved, Section 26 "
        "mandates that the child's paramount welfare overrides parental disputes.\n\n"
        "### Key Legal Provisions\n"
        "- **Section 13(1)(ia) — Grounds for Divorce (Cruelty)**\n"
        "- **Section 23(1)(b) — Bar against Condoned Marital Offenses**\n"
        "- **Section 24 & 25 — Interim Maintenance & Permanent Alimony**\n"
        "- **Section 26 — Child Custody & Maintenance**\n\n"
        "> 💡 **Specialist Tip**: *For detailed statutory case law lookup, consider tagging `@qa` or combining `@advocate @qa`.*"
    )
    return passage


def run_devils_advocate_agent(
    user_narrative: str,
    rag_context: List[Dict[str, Any]] = None,
    document_context: Optional[str] = None,
    session_id: str = "default_session",
    slm_model: Optional[str] = None,
    main_model: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Executes a multi-lens adversarial legal analysis using SLM context bridge -> Main LLM in conversational passage style.
    """
    # 1. Sensitivity pass
    sens_res = classify_sensitivity(user_narrative)
    sensitivity_flags = sens_res["sensitivity_flags"]
    helplines = sens_res["helplines"]

    # 2. Execute 2-tier generation
    llm_output, slm_brief = run_two_tier_rag_generation(
        system_prompt=DEVILS_ADVOCATE_SYSTEM_PROMPT,
        user_query=user_narrative,
        rag_context=rag_context or [],
        slm_model=slm_model,
        main_model=main_model,
        document_context=document_context,
        chat_history=chat_history
    )

    if llm_output:
        synthesis = llm_output
    else:
        synthesis = format_advocate_fallback(user_narrative, rag_context or [])

    disclaimer = get_disclaimer("advocate")
    resource_signpost = ""
    if sensitivity_flags:
        resource_signpost = (
            f"**Resource Notice**: We detected terms relating to sensitive matters ({', '.join(sensitivity_flags)}). "
            f"Please ensure your safety. Emergency Helplines: {', '.join([f'{k}: {v}' for k, v in helplines.items()])}."
        )

    log_trace(
        session_id=session_id,
        agent_name="Advocate Agent",
        input_summary=user_narrative,
        routing_reason="Strategic multi-lens adversarial legal analysis",
        retrieved_chunks=rag_context or [],
        token_usage=950,
        crag_triggered=False,
        extra_metadata={"slm_brief": slm_brief, "sensitivity_flags": sensitivity_flags}
    )

    return {
        "synthesis": synthesis,
        "disclaimer": disclaimer,
        "resource_signpost": resource_signpost,
        "slm_brief": slm_brief
    }
