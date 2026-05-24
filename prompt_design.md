# prompt_design.md — Closira AI Agent

**Candidate submission for AI Engineering Internship**  
**Project:** Bloom Aesthetics Clinic — AI Customer Support Workflow  
**Model:** LLaMA 3.3 70B (via Groq API)

---

## 1. System Prompt (Full)

```
You are Ivy, a professional and warm AI customer support assistant for Bloom Aesthetics Clinic.

Your role is to assist customers by answering questions, qualifying leads, and escalating when necessary.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE RULES (NON-NEGOTIABLE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ONLY answer from the SOP data provided. Never invent prices, services, policies, or facts.
2. If a question cannot be answered from the SOP, you MUST respond with the JSON flag:
   {"escalate": true, "reason": "<why>", "response": "<your message to customer>"}
3. If the customer seems angry, upset, or makes a complaint — escalate immediately.
4. If a customer asks for a medical opinion or health advice — escalate immediately.
5. If a customer wants to negotiate pricing — escalate immediately.
6. If a customer explicitly asks for a human — escalate immediately.
7. Do NOT speculate, estimate, or guess anything outside the SOP.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SOP DATA (your only source of truth):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Full SOP JSON injected at runtime]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For normal responses, reply in plain, friendly English. Keep it concise (2–4 sentences max).
For escalations, ALWAYS respond ONLY with valid JSON:
{"escalate": true, "reason": "REASON_TYPE", "response": "Your message to customer"}

REASON_TYPE must be one of:
COMPLAINT | MEDICAL_QUESTION | PRICING_NEGOTIATION | OUT_OF_SCOPE | ANGRY_SENTIMENT | EXPLICIT_HUMAN_REQUEST | REPEATED_UNKNOWN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TONE & PERSONA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Warm, professional, and reassuring
- Use the customer's name if known
- Never be robotic or use corporate jargon
- Sound like a knowledgeable, friendly clinic receptionist
- Keep responses brief — customers are often on mobile
```

---

## 2. Key Design Decisions & Reasoning

### 2.1 Persona: "Ivy"

Giving the AI a name (Ivy) serves two purposes:

1. **Trust-building** — SMB customers respond better to a named assistant than a generic "AI Bot"
2. **Consistency** — A defined persona keeps tone stable across multi-turn conversations

The name was chosen to feel feminine, professional, and natural for an aesthetics clinic context — similar to what a receptionist might be called.

### 2.2 SOP Injection at Runtime

The full SOP JSON is embedded directly into the system prompt rather than passed as a separate message. This approach:

- Keeps all grounding data in one authoritative location (the system prompt)
- Ensures the model sees the SOP *before* any conversation begins
- Makes it trivial to swap the SOP file for a different business without touching prompt logic

The SOP is structured as JSON with named keys (`services`, `hours`, `booking`, `escalation_rules`) to make it maximally parseable and searchable by the model.

### 2.3 Structured Escalation via JSON Output

Rather than using a soft instruction ("escalate if needed"), the system prompt **mandates a specific JSON format** for escalations:

```json
{"escalate": true, "reason": "REASON_TYPE", "response": "..."}
```

**Why this works:**
- It makes escalation machine-detectable (we parse the JSON in code, not text)
- The `REASON_TYPE` enum forces the model to categorise the escalation explicitly
- It separates the *internal reason* (for logging/CRM) from the *customer-facing message* (for display)
- It's reliable even across different model sizes and providers

A fallback regex parser handles cases where the model wraps JSON in markdown fences.

---

## 3. Hallucination Prevention

Three layered defences are used:

### Layer 1 — Explicit SOP grounding in system prompt
The instruction **"ONLY answer from the SOP data provided. Never invent prices, services, policies, or facts"** is in the non-negotiable rules section, formatted to stand out visually (using box-drawing characters) to maximise model attention.

### Layer 2 — Escalation as the safe fallback
Instead of saying "don't answer if unsure", we give the model a *clear action to take*: output the escalation JSON. This removes the temptation to hedge or guess, because escalation is explicitly the correct response for unknowns.

### Layer 3 — Keyword-based pre-screening
Before hitting the LLM, user messages are checked against a keyword dictionary for obvious escalation triggers (complaints, medical questions, pricing negotiation). This bypasses the model entirely for clear cases and eliminates any hallucination risk at the first line of defence.

### Layer 4 — Repeated-unknown counter
If the model responds with uncertainty phrases ("I don't have", "not in my information") more than once in a session, the workflow escalates automatically under the `REPEATED_UNKNOWN` reason. This prevents the model from becoming stuck in an uncertain loop.

---

## 4. Confidence-Based Escalation

Escalation triggers are defined at two levels:

### Hard rules (pre-LLM, keyword-based)
Matched against user input before any API call:

| Trigger | Keywords |
|---|---|
| `COMPLAINT` | "complaint", "disappointed", "unacceptable", "refund" |
| `MEDICAL_QUESTION` | "allergy", "side effect", "pregnant", "medical", "safe for me" |
| `ANGRY_SENTIMENT` | "furious", "ridiculous", "useless", "worst", "!!!" |
| `PRICING_NEGOTIATION` | "discount", "cheaper", "negotiate", "lower price" |
| `EXPLICIT_HUMAN_REQUEST` | "human", "real person", "agent", "manager", "speak to someone" |

Hard rules trigger escalation **without an API call**, keeping latency low and avoiding any model uncertainty.

### Soft rules (LLM-generated, via structured output)
The model itself can trigger escalation by returning the JSON flag. This catches nuanced cases (e.g., "Is this safe if I have a shellfish allergy?" doesn't match "medical" keyword but the model correctly flags it).

### Repeated-unknown threshold
`unknown_count` is tracked per session. Two consecutive unanswerable questions trigger `REPEATED_UNKNOWN` escalation. This mirrors the SOP rule: "Escalate if > 2 unanswered questions."

---

## 5. Tone and Persona

The persona instructions deliberately target the SMB context:

| Design choice | Rationale |
|---|---|
| "Warm, professional, reassuring" | Aesthetics clinics serve customers with appearance concerns — tone must feel safe and non-judgmental |
| "Never robotic or corporate jargon" | SMB customers expect a human-like experience; robotic responses break trust |
| "Keep responses brief — customers are often on mobile" | Most inbound messages to SMBs come via WhatsApp/mobile; long responses are skipped |
| "Use the customer's name if known" | Personalisation increases engagement and trust for SMB customers |
| "Sound like a friendly clinic receptionist" | This mental model keeps the AI grounded in what's appropriate to say vs. defer |

---

## 6. Multi-Stage Architecture

The four stages are separated in code (not just prompt):

```
Stage 1: FAQ Answering       → src/agent.py :: answer_faq()
Stage 2: Lead Qualification  → src/agent.py :: get_next_qualification_question()
Stage 3: Escalation          → src/agent.py :: check_keyword_escalation() + LLM JSON output
Stage 4: Summary             → src/agent.py :: generate_summary()
```

Separation ensures each stage is independently testable and replaceable. The workflow orchestrator (`src/workflow.py`) manages transitions between stages using a simple state machine (`Stage` enum in `src/session.py`).

Qualification is triggered automatically after the customer's first meaningful response, to ensure we capture lead data early in every session.

---

## 7. Trade-offs and Known Limitations

| Limitation | Trade-off made |
|---|---|
| In-memory session store | Simple to run locally; swap to Redis for production multi-user deployments |
| Keyword matching is literal | Fast and reliable; misses paraphrases. Mitigated by LLM-level escalation as backup |
| LLM temperature set to 0.2 | Prioritises consistency over creativity — appropriate for factual SOP responses |
| No streaming | Simpler to implement; add SSE streaming for production to improve perceived latency |
| Single SOP file | Trivially replaced or extended; a production system would pull from a database |
| Groq rate limits | Free tier has usage limits; upgrade to paid or add retry logic for production |

---

*Document version: 1.0 | Closira AI Engineering Internship Submission*
