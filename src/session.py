"""
Session Manager — Manages conversation state across the 4 stages.
"""

import uuid
import datetime
from typing import Optional
from enum import Enum


class Stage(str, Enum):
    FAQ = "faq"
    QUALIFICATION = "qualification"
    ESCALATED = "escalated"
    SUMMARY = "summary"


class ConversationSession:
    def __init__(self):
        self.session_id: str = str(uuid.uuid4())[:8].upper()
        self.started_at: str = datetime.datetime.now().isoformat()
        self.history: list = []  # OpenAI-format messages
        self.stage: Stage = Stage.FAQ
        self.qualification_answers: dict = {}
        self.qualification_questions_asked: int = 0
        self.escalation_log: Optional[dict] = None
        self.unknown_count: int = 0  # Tracks consecutive unanswerable questions
        self.customer_name: Optional[str] = None
        self.summary: Optional[dict] = None
        self.sop_gaps: list[dict] = []  # Detected SOP coverage gaps

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})

    def set_escalated(self, reason: str, log: dict):
        self.stage = Stage.ESCALATED
        self.escalation_log = log

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "stage": self.stage.value,
            "history": self.history,
            "qualification_answers": self.qualification_answers,
            "escalation_log": self.escalation_log,
            "summary": self.summary,
            "sop_gaps": self.sop_gaps,
        }
