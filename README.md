# Vivaha — AI-Powered Matrimonial Legal Assistant

> *Vivaha* (Sanskrit: विवाह) — the sacred bond. Vivaha helps individuals navigate the legal complexities of matrimonial disputes with clarity, confidence, and grounded legal reasoning.

---

## Chosen Vertical

**Legal Information Accessibility — Matrimonial / Family Law**

Vivaha addresses one of the most emotionally charged and legally complex domains in Indian civil law: matrimonial disputes under the **Hindu Marriage Act 1955 (HMA)** and the **Special Marriage Act 1954 (SMA)**. These two acts together cover the largest segment of the Indian population and generate some of the highest volumes of civil litigation in Indian courts.

Legal help in this domain is often inaccessible — expensive, intimidating, and opaque. Vivaha makes it accessible.

---

## Problem Statement

When individuals face matrimonial disputes, they are typically:
- Confronted with dense legal language they cannot parse
- Unaware of their rights, risks, and options under HMA/SMA
- Blind to the arguments the opposing party could make
- Unable to afford a consultation before understanding their own situation
- Dependent on generic internet searches that give unreliable, ungrounded information

Vivaha solves all five of these problems in a single, integrated session.

---

## Approach and Logic

### Architecture: Orchestrator + Specialist Sub-Agents + Hybrid RAG

Vivaha is built on a **multi-agent architecture** orchestrated by a LangGraph state machine. Each user query is classified by the Orchestrator and routed to the appropriate specialist agent. Agents are grounded exclusively in retrieved legal context — they do not generate legal facts independently.

```
User Input
    │
    ▼
Orchestrator (LangGraph)
    │
    ├── Sensitivity Classifier ──► Crisis escalation (if needed)
    │
    ├──► Simplifier Agent       — Plain-language legal translation
    ├──► Risk Spotter Agent     — Clause risk flagging (High/Medium/Low)
    ├──► Comparator Agent       — Document/narrative diff (3 modes)
    ├──► Q&A Agent              — Grounded question answering
    └──► Devil's Advocate Agent — Adversarial multi-lens legal analysis
              │
              ├── Mode A: Opposing party's strongest arguments
              ├── Mode B: Stress-test of user's own narrative
              └── Mode C: Judicial / mediator perspective
```

### RAG Architecture: Hybrid BM25 + Semantic + Reranker + CRAG

Retrieval is the backbone of Vivaha's reliability:

1. **BM25 (lexical)** — exact term matching for legal section references (e.g., "Section 13", "restitution of conjugal rights")
2. **Semantic search** — embedding-based retrieval for conceptual queries (e.g., "what happens to my assets?")
3. **Reciprocal Rank Fusion (RRF)** — merges BM25 and semantic rankings into a single list
4. **Cross-encoder reranker** — refines top-k results by relevance to the exact query
5. **Corrective RAG (CRAG)** — if top retrieval score < 0.55, query is automatically reformulated and retrieval retried before any LLM narration occurs

This ensures: **no hallucinated legal facts**. If the corpus doesn't contain a reliable answer, Vivaha says so and recommends consulting a legal professional.

### The Devil's Advocate — The Headline Feature

Most legal AI tools answer questions. Vivaha goes further: it shows users what they *don't* want to see but *need* to see before walking into a consultation.

The Devil's Advocate agent runs three internal reasoning passes on the user's narrative or document:

- **Mode A — Opposing Arguments**: "If your spouse hired a lawyer today, here are the strongest arguments they would make against your position, grounded in HMA/SMA provisions and case law."
- **Mode B — Narrative Stress-Test**: "Here are the weaknesses in your own account — inconsistencies, missing documentation, and vulnerabilities a court or opposing counsel would exploit."
- **Mode C — Judicial Lens**: "Here is what a family court judge or mediator typically weighs in disputes like yours — neither your perspective nor your spouse's, but the court's."

Every argument is cited. No precedent is invented. If no case law matches, the agent says so.

---

## How the Solution Works

### User Flow

1. User opens Vivaha in the browser (Streamlit Link)
2. User types a question or uploads a document (PDF / DOCX / TXT)
3. Orchestrator classifies intent and routes to appropriate agent(s)
4. Agent retrieves grounded legal context via hybrid RAG
5. Agent narrates a response grounded entirely in retrieved text
6. Response is displayed with citations, a disclaimer, and an optional "Show Reasoning" panel
7. User rates the response (thumbs up / thumbs down) with optional comment
8. For documents with sensitive topics (custody, domestic violence), helpline signposting is immediate

### Reasoning Panel (Chain of Thought Observability)

Every response includes a collapsible **"Show Reasoning"** panel that exposes:
- Which agent(s) were invoked and why
- Retrieved legal chunks (top 3) with source and reranker score
- Whether CRAG was triggered
- Token usage for the turn

This makes Vivaha's reasoning fully auditable — for evaluators, for legal professionals reviewing outputs, and for users who want to understand the basis of every answer.

---

## Assumptions Made

1. **Jurisdiction**: India only. HMA 1955 + SMA 1954. No other personal law acts are in scope for this submission.
2. **Corpus**: Built from public domain sources (legislative.gov.in bare acts, Indian Kanoon closed case law) and clearly tagged synthetic template documents. No proprietary legal databases.
3. **Not legal advice**: Every output carries a hard disclaimer. Vivaha provides information and analysis — not legal advice, not prediction of court outcomes, not document execution services.
4. **LLM role**: LLMs narrate pre-retrieved grounded context only. They do not generate legal facts, invent precedents, or speculate beyond what the RAG corpus contains.
5. **Document size**: Maximum 10 MB per uploaded document (aligned with repo constraint).
6. **Language**: English primary. Hinglish simplification available as an accessibility option in the Simplifier agent.
7. **Sensitivity handling**: Emotional distress signals (domestic violence, mental health) trigger immediate helpline signposting. Vivaha is not a crisis service — it directs users to appropriate resources.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | LangGraph (Python) |
| LLM | OpenRouter API (model-agnostic; configured via environment variable) |
| Embedding | sentence-transformers/all-MiniLM-L6-v2 (local, free) |
| Vector Store | FAISS (local, CPU) |
| Lexical Retrieval | rank_bm25 |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 (local, free) |
| Document Parsing | pdfminer-six, python-docx, pytesseract |
| UI | Streamlit |
| Hosting | HuggingFace Spaces (free tier) |
| Testing | pytest |

---

## Project Structure

```
vivaha/
├── agents/
│   ├── orchestrator.py
│   ├── simplifier.py
│   ├── risk_spotter.py
│   ├── comparator.py
│   ├── qa_agent.py
│   └── devils_advocate.py
├── skills/
│   ├── document_ingestion.py
│   ├── rag_pipeline.py
│   ├── crag.py
│   ├── risk_classification.py
│   ├── disclaimer.py
│   ├── observability.py
│   ├── feedback_collector.py
│   └── sensitivity_classifier.py
├── data/
│   └── corpus/
│       └── sample/          ← Representative corpus samples (evaluator demo)
├── tests/
│   ├── test_orchestrator.py
│   ├── test_simplifier.py
│   ├── test_risk_spotter.py
│   ├── test_comparator.py
│   ├── test_qa.py
│   ├── test_devils_advocate.py
│   ├── test_rag_pipeline.py
│   ├── test_crag.py
│   ├── test_document_ingestion.py
│   ├── test_risk_classification.py
│   ├── test_disclaimer.py
│   ├── test_observability.py
│   ├── test_feedback_collector.py
│   └── test_sensitivity_classifier.py
├── app.py                   ← Streamlit entry point
├── requirements.txt
├── agents.md
├── skills.md
├── progress.md
├── dependencies.md
├── masterskills-index.md
├── data_sources.md
├── README.md
└── .gitignore
```

---

## Running Locally

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/vivaha.git
cd vivaha

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install system dependency for OCR (optional — for scanned PDF support)
# Ubuntu/Debian: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract

# 4. Set environment variables
cp .env.example .env
# Edit .env: add your OPENROUTER_API_KEY and OPENROUTER_MODEL

# 5. Build the corpus index (first run)
python scripts/build_index.py

# 6. Run the app
streamlit run app.py
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Deployment (HuggingFace Spaces)

1. Create a new Space on HuggingFace (Streamlit type)
2. Add `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` as **Space Secrets** (Settings → Repository Secrets)
3. Push the repository — Spaces builds automatically from `app.py` and `requirements.txt`
4. FAISS index is built at cold start from corpus files in `data/corpus/`

---

## Safety and Disclaimer

> **This application provides legal information for educational purposes only. It does not constitute legal advice. Always review any documents or information with a qualified legal professional before taking any action.**

Vivaha is designed with safety as a first principle:
- Hard disclaimers on every output (non-dismissable)
- No hallucinated legal facts — retrieval-grounded only
- Immediate helpline signposting for sensitive situations
- PII redaction in all logs and traces
- No legal documents are executed or certified through this application

**Crisis resources**: If you or someone you know is experiencing distress, please contact **iCall** at **9152987821** or **SNEHI** at **011-65978181**.

---

## Author

**Shawn (S Sukhvinder Singh)**
Submission for the Prompt Wars Hackathon — Legal Accessibility Vertical
