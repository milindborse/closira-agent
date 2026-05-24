"""
Closira AI Agent — Core Logic
Handles: FAQ Answering, Lead Qualification, Escalation Detection, Conversation Summary
Model: Uses Groq API (llama-3.3-70b-versatile)
"""

import json
import os
import re
import datetime
from typing import Any, Optional
from groq import Groq

# ─── Load SOP ────────────────────────────────────────────────────────────────

def load_sop(path: str = "sop_data.json") -> dict:
    with open(path, "r") as f:
        return json.load(f)

SOP = load_sop()
SOP_TEXT = json.dumps(SOP, indent=2)


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "could",
    "do",
    "does",
    "for",
    "from",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "please",
    "the",
    "their",
    "they",
    "to",
    "us",
    "we",
    "what",
    "when",
    "where",
    "with",
    "you",
    "your",
}


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9']+", text.lower()) if t and t not in _STOPWORDS]


def _flatten_sop_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if obj is None:
        return out
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, (int, float, bool)):
        out.append(str(obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.append(str(k))
            out.extend(_flatten_sop_strings(v))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(_flatten_sop_strings(item))
    else:
        out.append(str(obj))
    return out


def _build_sop_keyword_set(sop: dict) -> set[str]:
    tokens: set[str] = set()
    for s in _flatten_sop_strings(sop):
        for t in _tokenize(s):
            tokens.add(t)
    return tokens


SOP_KEYWORDS = _build_sop_keyword_set(SOP)


def compute_confidence(
    user_message: str,
    ai_message: str,
    *,
    escalated: bool,
    escalation_reason: Optional[str] = None,
) -> float:
    """Heuristic confidence score in [0,1].

    Goal: expose a stable, explainable signal for UI and SOP-gap detection.
    (We avoid logprobs/vendor-specific confidence APIs for portability.)
    """
    if escalated:
        # Escalation means "I cannot answer from SOP".
        return 0.0

    q_tokens = _tokenize(user_message)
    if not q_tokens:
        return 0.4

    hit = sum(1 for t in q_tokens if t in SOP_KEYWORDS)
    coverage = hit / max(len(q_tokens), 1)

    ai_lower = ai_message.lower()
    uncertainty_phrases = [
        "i think",
        "maybe",
        "might",
        "not sure",
        "cannot find",
        "can't find",
        "unable to",
        "don't have",
        "do not have",
        "not in my information",
        "not in the sop",
    ]
    uncertainty = 1.0 if any(p in ai_lower for p in uncertainty_phrases) else 0.0

    numeric_boost = 0.05 if re.search(r"\b(£|gbp|\d{2,})\b", ai_lower) else 0.0

    score = 0.55 + 0.4 * coverage + numeric_boost - 0.25 * uncertainty

    # Minor adjustment for reasons that still returned a normal answer.
    if escalation_reason in {"OUT_OF_SCOPE", "REPEATED_UNKNOWN"}:
        score -= 0.15

    return max(0.0, min(1.0, score))


def detect_sop_gap(
    user_message: str,
    ai_message: str,
    *,
    escalated: bool,
    escalation_reason: Optional[str],
    confidence: float,
    soft_threshold: float = 0.45,
) -> Optional[dict]:
    """Return a SOP gap record (dict) when detected, else None."""

    hard_reasons = {"OUT_OF_SCOPE", "REPEATED_UNKNOWN"}
    if escalated and escalation_reason in hard_reasons:
        return {
            "question": user_message,
            "kind": "hard",
            "reason": escalation_reason,
            "confidence": confidence,
        }

    # Soft gap: answered, but looks weak / likely not grounded.
    ai_lower = ai_message.lower()
    soft_markers = [
        "not in my information",
        "not in the sop",
        "unable to",
        "can't find",
        "cannot find",
        "i don't have",
        "do not have",
    ]

    if confidence < soft_threshold or any(m in ai_lower for m in soft_markers):
        return {
            "question": user_message,
            "kind": "soft",
            "reason": "LOW_CONFIDENCE",
            "confidence": confidence,
        }

    return None

# ─── Groq Client ─────────────────────────────────────────────────────────────

def get_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")
    return Groq(api_key=api_key)

# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
"""You are Ivy, a professional and warm AI customer support assistant for Bloom Aesthetics Clinic.

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

"""
+ SOP_TEXT +
"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For normal responses, reply in plain, friendly English. Keep it concise (2-4 sentences max).
For escalations, ALWAYS respond ONLY with valid JSON:
{"escalate": true, "reason": "REASON_TYPE", "response": "Your message to customer"}

REASON_TYPE must be one of: COMPLAINT, MEDICAL_QUESTION, PRICING_NEGOTIATION, OUT_OF_SCOPE, ANGRY_SENTIMENT, EXPLICIT_HUMAN_REQUEST, REPEATED_UNKNOWN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TONE & PERSONA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Warm, professional, and reassuring
- Use the customer's name if known
- Never be robotic or use corporate jargon
- Sound like a knowledgeable, friendly clinic receptionist
- Keep responses brief — customers are often on mobile

You are Ivy. Begin each new session with a warm greeting.
"""
)

# ─── Lead Qualification Questions ────────────────────────────────────────────

QUALIFICATION_QUESTIONS = [
    "To help us prepare for your visit, could you let me know which treatment you're most interested in — Botox, Fillers, or a general consultation?",
    "Have you had any aesthetic treatments done before, or would this be your first time?",
    "Are you looking to book for yourself, or are you enquiring on behalf of someone else?"
]

# ─── Stage 1: FAQ Answering ───────────────────────────────────────────────────

def answer_faq(client: Groq, conversation_history: list) -> dict:
    """
    Sends the conversation to the model and returns a structured response.
    Detects escalation via JSON in response.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        max_tokens=512
    )

    raw = response.choices[0].message.content.strip()

    # Detect escalation JSON
    escalation = _try_parse_escalation(raw)
    if escalation:
        return {"type": "escalation", "data": escalation, "raw": raw}

    return {"type": "answer", "raw": raw}


def _try_parse_escalation(text: str) -> Optional[dict]:
    """Attempt to parse escalation JSON from model response."""
    try:
        # Try direct parse
        data = json.loads(text)
        if data.get("escalate") is True:
            return data
    except json.JSONDecodeError:
        pass

    # Try extracting JSON block from mixed text
    match = re.search(r'\{.*?"escalate"\s*:\s*true.*?\}', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if data.get("escalate") is True:
                return data
        except json.JSONDecodeError:
            pass

    return None


# ─── Stage 2: Lead Qualification ─────────────────────────────────────────────

def get_next_qualification_question(asked_count: int) -> Optional[str]:
    """Returns the next qualification question, or None if all asked."""
    if asked_count < len(QUALIFICATION_QUESTIONS):
        return QUALIFICATION_QUESTIONS[asked_count]
    return None


# ─── Stage 3: Escalation ─────────────────────────────────────────────────────

ESCALATION_KEYWORDS = {
    "COMPLAINT": ["complaint", "disappointed", "unacceptable", "terrible", "awful", "disgusting", "refund", "this is a joke"],
    "MEDICAL_QUESTION": ["allergy", "allergic", "side effect", "reaction", "medication", "pregnant", "medical", "doctor", "safe for me", "health condition"],
    "ANGRY_SENTIMENT": ["angry", "furious", "ridiculous", "pathetic", "useless", "waste of time", "!!!", "worst", "never coming back"],
    "PRICING_NEGOTIATION": ["discount", "cheaper", "negotiate", "lower price", "deal", "offer", "beat the price", "match the price"],
    "EXPLICIT_HUMAN_REQUEST": ["speak to someone", "human", "real person", "agent", "manager", "call me", "speak to a human"]
}


def check_keyword_escalation(user_message: str) -> Optional[dict]:
    """Fast keyword-based pre-check for obvious escalation triggers."""
    msg_lower = user_message.lower()
    for reason, keywords in ESCALATION_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                return {
                    "escalate": True,
                    "reason": reason,
                    "response": _escalation_message(reason)
                }
    return None


def _escalation_message(reason: str) -> str:
    messages = {
        "COMPLAINT": "I'm really sorry to hear that. I'm going to connect you with a member of our team right away so they can assist you properly.",
        "MEDICAL_QUESTION": "That's a great question, and for your safety I'd like to connect you with one of our qualified practitioners who can give you accurate guidance.",
        "ANGRY_SENTIMENT": "I sincerely apologise for your experience. Let me connect you with a senior team member immediately.",
        "PRICING_NEGOTIATION": "I appreciate you asking — pricing discussions are best handled by our team directly. Let me connect you with them now.",
        "EXPLICIT_HUMAN_REQUEST": "Of course! I'm connecting you to a human agent right now. They'll be with you shortly.",
        "REPEATED_UNKNOWN": "I want to make sure you get the best help possible. Let me connect you with our team who can answer this properly.",
        "OUT_OF_SCOPE": "That's outside what I can help with directly. Let me connect you with our team who will be happy to assist."
    }
    return messages.get(reason, "Let me connect you with a member of our team who can help.")


def log_escalation(reason: str, conversation_history: list, session_id: str) -> dict:
    """Logs escalation event to a structured dict."""
    return {
        "session_id": session_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "escalation_reason": reason,
        "conversation_length": len(conversation_history),
        "last_user_message": next(
            (m["content"] for m in reversed(conversation_history) if m["role"] == "user"), ""
        )
    }


# ─── Stage 4: Conversation Summary ───────────────────────────────────────────

SUMMARY_PROMPT = """You are a CRM assistant. Analyze this customer support conversation and generate a structured JSON summary.

Conversation:
{conversation}

Respond ONLY with this JSON (no other text):
{{
  "customer_intent": "What the customer primarily wanted",
  "services_mentioned": ["list of services discussed"],
  "qualification_data": {{
    "treatment_interest": "...",
    "previous_treatments": "...",
    "booking_for": "..."
  }},
  "sop_gaps": ["Any questions the AI could not answer from SOP"],
  "escalated": true/false,
  "escalation_reason": "reason or null",
  "sentiment": "positive/neutral/negative",
  "recommended_next_action": "What the human team should do next",
  "session_duration_turns": {turns}
}}"""


def generate_summary(
    client: Groq,
    conversation_history: list,
    escalation_log: Optional[dict] = None,
    detected_sop_gaps: Optional[list[str]] = None,
) -> dict:
    """Generates a structured end-of-session summary."""
    convo_text = "\n".join(
        f"{'Customer' if m['role'] == 'user' else 'Ivy (AI)'}: {m['content']}"
        for m in conversation_history
    )

    turns = len([m for m in conversation_history if m["role"] == "user"])

    prompt = SUMMARY_PROMPT.format(conversation=convo_text, turns=turns)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600
    )

    raw = response.choices[0].message.content.strip()

    try:
        summary = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON block
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                summary = json.loads(match.group())
            except Exception:
                summary = {"error": "Could not parse summary", "raw": raw}
        else:
            summary = {"error": "Could not parse summary", "raw": raw}

    if escalation_log:
        summary["escalation_log"] = escalation_log

    if detected_sop_gaps:
        existing = summary.get("sop_gaps")
        if not isinstance(existing, list):
            existing = []
        merged = []
        for item in [*existing, *detected_sop_gaps]:
            if isinstance(item, str) and item.strip() and item not in merged:
                merged.append(item)
        summary["sop_gaps"] = merged

    return summary
