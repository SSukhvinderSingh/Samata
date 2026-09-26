# Samata — System Architecture & Multi-Agent Deliberation Suite 🏛️

## 1. High-Level Architecture Diagram

```mermaid
graph TD
    User([👤 User / Citizen]) --> UI[🖥️ Streamlit High-Contrast Chambers UI]
    UI --> Router[🔀 Orchestrator & Intent Router]
    
    subgraph Safety & Triage [Tier 0: Safety & Sensitivity]
        Router --> SafetyClassifier{🚨 Crisis / Threat Detected?}
        SafetyClassifier -->|Yes| CrisisHelpline[National Helplines: iCall, SNEHI, NCW]
    end

    subgraph SLM Tier [Tier 1: SLM Llama 3.2 3B]
        Router --> IntentDispatch[Agent Dispatcher & Context Distiller]
        IntentDispatch --> RAGRetrieval[Hybrid Search: BM25 + Dense RRF + Cross-Encoder]
    end

    subgraph LLM Specialist Agents [Tier 2: LLM Llama 3.3 70B Reasoning]
        RAGRetrieval --> QA[📖 Statutory Q&A Agent]
        RAGRetrieval --> Advocate[⚖️ Strategic Advocate Agent]
        RAGRetrieval --> Risk[🚩 Deed & Risk Spotter Agent]
        RAGRetrieval --> Simplify[🗣️ Plain Language / Hinglish Simplifier]
        RAGRetrieval --> Compare[📊 Legal Comparator Agent]
        
        QA --> Deliberation[🤝 Multi-Agent Deliberation Panel]
        Advocate --> Deliberation
        Risk --> Deliberation
    end

    Deliberation --> Sanitizer[🛡️ PII Scrubber & Disclaimer Injector]
    Sanitizer --> ResponseStream[📤 Verified Response Docket + Reasoning Trace]
    ResponseStream --> UI
```

---

## 2. Multi-Agent Deliberation Pipeline

When complex queries or separation agreements are submitted, the Orchestrator supports **Multi-Agent Tagging** (e.g. `@risk @advocate`).

1. **Step 1 — Risk Spotter Audit**: Identifies one-sided waiver clauses, statutory bars under Section 23/25 HMA, and adverse forfeiture terms.
2. **Step 2 — Strategic Advocate Cross-Evaluation**: Takes the flagged risks and stress-tests them from opposing counsel's perspective, highlighting evidentiary vulnerabilities and counter-claims.
3. **Step 3 — Synthesis & Docket Delivery**: Merges the findings into an actionable, color-coded courtroom briefing with clear disclaimers.

---

## 3. Data Flow & Security Boundaries
- **Ephemeral Session State**: Sessions exist solely in-memory (`st.session_state`) and terminate upon browser closure.
- **Zero Raw LLM Pass-Through**: All responses pass through statutory citation grounding and educational disclaimers.
