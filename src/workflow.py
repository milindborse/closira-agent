"""Closira Workflow Orchestrator
Ties together all 4 stages into a single, clean pipeline.
"""

import json
import datetime
from typing import Optional
from src.agent import (
    get_groq_client, answer_faq, check_keyword_escalation,
    get_next_qualification_question, log_escalation, generate_summary,
    _escalation_message, compute_confidence, detect_sop_gap
)
from src.session import ConversationSession, Stage
from src.logging_utils import append_jsonl, get_logger, log_event


class ClosiraWorkflow:
    def __init__(self):
        self.client = get_groq_client()
        self.session = ConversationSession()
        self._greeting_sent = False
        self.logger = get_logger()
        log_event("session_started", {"session_id": self.session.session_id})

    def get_greeting(self) -> str:
        self._greeting_sent = True
        greeting = (
            "👋 Hello! I'm **Ivy**, your AI assistant at **Bloom Aesthetics Clinic**. "
            "I'm here to help you with information about our services, bookings, and more. "
            "What can I help you with today?"
        )
        self.session.add_assistant_message(greeting)
        return greeting

    def process_message(self, user_input: str) -> dict:
        """
        Main entry point. Returns a structured response dict:
        {
            "message": str,
            "stage": str,
            "escalated": bool,
            "escalation_reason": str | None,
            "show_qualification": bool,
            "summary": dict | None
        }
        """
        user_input = user_input.strip()
        if not user_input:
            return self._response("I didn't quite catch that. Could you please rephrase?")

        self.session.add_user_message(user_input)
        log_event(
            "user_message",
            {
                "session_id": self.session.session_id,
                "message": user_input,
                "stage": self.session.stage.value,
            },
        )

        # ── Already escalated ──────────────────────────────────────────────
        if self.session.stage == Stage.ESCALATED:
            return self._response(
                "Our team has been notified and will be in touch shortly. "
                "Is there anything else I can note down for them?",
                escalated=True,
                escalation_reason=self.session.escalation_log.get("escalation_reason") if self.session.escalation_log else None,
                confidence=0.0,
            )

        # ── Stage 1 & 3: Check keywords for fast escalation ───────────────
        keyword_escalation = check_keyword_escalation(user_input)
        if keyword_escalation:
            return self._handle_escalation(keyword_escalation)

        # ── Stage 2: Lead Qualification ────────────────────────────────────
        if self.session.stage == Stage.QUALIFICATION:
            return self._handle_qualification(user_input)

        # ── Trigger qualification after first meaningful exchange ──────────
        user_turns = len([m for m in self.session.history if m["role"] == "user"])
        if user_turns == 2 and self.session.qualification_questions_asked == 0:
            next_q = get_next_qualification_question(0)
            self.session.stage = Stage.QUALIFICATION
            self.session.qualification_questions_asked = 0
            self.session.add_assistant_message(next_q)
            return self._response(
                next_q,
                show_qualification=True
            )

        # ── Stage 1: FAQ Answering ─────────────────────────────────────────
        result = answer_faq(self.client, self.session.history)

        if result["type"] == "escalation":
            return self._handle_escalation(result["data"])

        # Check for repeated unknowns
        raw_lower = result["raw"].lower()
        if any(phrase in raw_lower for phrase in ["i don't have", "not in my information", "can't find", "unable to answer"]):
            self.session.unknown_count += 1
            if self.session.unknown_count >= 2:
                return self._handle_escalation({
                    "escalate": True,
                    "reason": "REPEATED_UNKNOWN",
                    "response": _escalation_message("REPEATED_UNKNOWN")
                })
        else:
            self.session.unknown_count = 0

        confidence = compute_confidence(user_input, result["raw"], escalated=False)
        gap = detect_sop_gap(
            user_input,
            result["raw"],
            escalated=False,
            escalation_reason=None,
            confidence=confidence,
        )
        if gap:
            record = {
                "session_id": self.session.session_id,
                "timestamp": datetime.datetime.now().isoformat(),
                **gap,
            }
            self.session.sop_gaps.append(record)
            append_jsonl("sop_gaps.jsonl", record)
            log_event("sop_gap_detected", {"session_id": self.session.session_id, **gap})

        self.session.add_assistant_message(result["raw"])
        log_event(
            "assistant_message",
            {
                "session_id": self.session.session_id,
                "message": result["raw"],
                "stage": self.session.stage.value,
                "confidence": confidence,
            },
        )

        return self._response(
            result["raw"],
            confidence=confidence,
            sop_gap=gap,
        )

    def _handle_qualification(self, user_input: str) -> dict:
        """Stores qualification answer and asks next question."""
        q_index = self.session.qualification_questions_asked
        q_keys = ["treatment_interest", "previous_treatments", "booking_for"]

        if q_index < len(q_keys):
            self.session.qualification_answers[q_keys[q_index]] = user_input
            self.session.qualification_questions_asked += 1

        next_q = get_next_qualification_question(self.session.qualification_questions_asked)

        if next_q:
            self.session.add_assistant_message(next_q)
            return self._response(next_q, show_qualification=True, confidence=1.0)
        else:
            # Done — return to FAQ mode
            self.session.stage = Stage.FAQ
            done_msg = (
                "Thank you for sharing that! I've noted your preferences. "
                "Feel free to ask me anything else about our treatments or to book an appointment. 😊"
            )
            self.session.add_assistant_message(done_msg)
            return self._response(done_msg, confidence=1.0)

    def _handle_escalation(self, escalation_data: dict) -> dict:
        reason = escalation_data.get("reason", "OUT_OF_SCOPE")
        customer_message = escalation_data.get("response", _escalation_message(reason))

        confidence = compute_confidence(
            next((m["content"] for m in reversed(self.session.history) if m["role"] == "user"), ""),
            customer_message,
            escalated=True,
            escalation_reason=reason,
        )

        gap = detect_sop_gap(
            next((m["content"] for m in reversed(self.session.history) if m["role"] == "user"), ""),
            customer_message,
            escalated=True,
            escalation_reason=reason,
            confidence=confidence,
        )
        if gap:
            record = {
                "session_id": self.session.session_id,
                "timestamp": datetime.datetime.now().isoformat(),
                **gap,
            }
            self.session.sop_gaps.append(record)
            append_jsonl("sop_gaps.jsonl", record)
            log_event("sop_gap_detected", {"session_id": self.session.session_id, **gap})

        log = log_escalation(reason, self.session.history, self.session.session_id)
        self.session.set_escalated(reason, log)
        self.session.add_assistant_message(customer_message)

        log_event(
            "escalation",
            {
                "session_id": self.session.session_id,
                "reason": reason,
                "confidence": confidence,
            },
        )

        return self._response(
            customer_message,
            escalated=True,
            escalation_reason=reason,
            confidence=confidence,
            sop_gap=gap,
        )

    def generate_session_summary(self) -> dict:
        """Triggers Stage 4: Conversation Summary."""
        detected = []
        for g in self.session.sop_gaps:
            q = g.get("question")
            if isinstance(q, str) and q.strip() and q not in detected:
                detected.append(q)

        summary = generate_summary(
            self.client,
            self.session.history,
            self.session.escalation_log,
            detected_sop_gaps=detected or None,
        )
        self.session.summary = summary
        self.session.stage = Stage.SUMMARY
        log_event("session_summary_generated", {"session_id": self.session.session_id})
        return summary

    def _response(
        self,
        message: str,
        escalated: bool = False,
        escalation_reason: str = None,
        show_qualification: bool = False,
        summary: dict = None,
        confidence: Optional[float] = None,
        sop_gap: Optional[dict] = None,
    ) -> dict:
        return {
            "message": message,
            "stage": self.session.stage.value,
            "session_id": self.session.session_id,
            "escalated": escalated,
            "escalation_reason": escalation_reason,
            "show_qualification": show_qualification,
            "summary": summary,
            "confidence": confidence,
            "sop_gap": sop_gap,
            "history_length": len(self.session.history)
        }

    def get_session_data(self) -> dict:
        return self.session.to_dict()
