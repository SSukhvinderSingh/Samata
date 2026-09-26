# Security & Responsible AI Policy — Samata

## 1. Safety & Ethical Mandate
Samata is an AI-powered legal information assistant engineered with safety, ethical grounding, and citizen protection as first principles.

### Zero-Data Retention & Privacy
- **Local Ephemeral Index**: All corpus retrieval is executed locally against indexed statute chunks.
- **Zero Prompt Storage**: User narratives, uploaded deeds, and consultation chats are not stored permanently or shared with external model trainers.
- **Secret Isolation**: Live API keys (`OPENROUTER_API_KEY`) reside exclusively in encrypted runtime environment secrets managers and are never exposed in logs or client-side bundles.

---

## 2. PII Redaction & Sanitization
All observability traces and feedback logs pass through strict regex and NLP anonymization filters before persistence:
- **Phone Numbers**: Automatically masked (e.g. `XXXXX-XXXXX`).
- **Email Addresses**: Automatically masked (e.g. `[EMAIL_REDACTED]`).
- **Aadhaar / Identity IDs**: Pattern-matched and redacted prior to trace generation.

---

## 3. Prompt Injection & Adversarial Defense
- **Input Sanitization**: User inputs are sanitized to prevent prompt breakout and XML boundary evasion.
- **Output Validation**: Responses are scanned to strip internal system tags (e.g. `<slm_legal_research_brief>`) and prevent raw score or filename leakage.

---

## 4. Emergency & Distress Protocols
- **Immediate Helpline Routing**: Queries involving domestic violence, self-harm, or child safety trigger non-dismissable crisis helpline routing (e.g. **iCall 9152987821**, **SNEHI 011-65978181**, **NCW 7827170170**).
