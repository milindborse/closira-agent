"""
Closira CLI — Run the AI agent in your terminal.
Usage: python cli.py
"""

import os
import json
import sys
from typing import Optional
from src.workflow import ClosiraWorkflow

# ── Colours ────────────────────────────────────────────────────────────────────
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def print_banner():
    print(f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════════════════╗
║         CLOSIRA AI AGENT — BLOOM AESTHETICS          ║
║         Powered by Groq + LLaMA 3.3 70B              ║
╚══════════════════════════════════════════════════════╝
{RESET}""")


def print_ivy(message: str):
    clean = message.replace("**", "").replace("*", "")
    print(f"\n{CYAN}{BOLD}🌸 Ivy:{RESET} {clean}")


def print_meta(confidence: Optional[float] = None, sop_gap: Optional[dict] = None):
    meta_parts = []
    if confidence is not None:
        meta_parts.append(f"Confidence: {round(confidence * 100)}%")
    if sop_gap:
        kind = sop_gap.get("kind")
        meta_parts.append(f"SOP gap logged ({kind})")
    if meta_parts:
        print(f"{DIM}   {' · '.join(meta_parts)}{RESET}")


def print_user(message: str):
    print(f"{GREEN}{BOLD}You:{RESET} {message}")


def print_escalation(reason: str):
    print(f"\n{RED}{BOLD}⚠️  ESCALATION TRIGGERED{RESET}")
    print(f"{DIM}   Reason: {reason}{RESET}")
    print(f"{DIM}   This conversation has been flagged for human agent handoff.{RESET}")


def print_summary(summary: dict):
    print(f"\n{YELLOW}{BOLD}{'─'*55}")
    print("  📋  CONVERSATION SUMMARY")
    print(f"{'─'*55}{RESET}")
    print(json.dumps(summary, indent=2))
    print(f"{YELLOW}{'─'*55}{RESET}\n")


def main():
    print_banner()

    if not os.environ.get("GROQ_API_KEY"):
        print(f"{RED}Error: GROQ_API_KEY environment variable not set.{RESET}")
        print("Set it with: export GROQ_API_KEY=your_key_here")
        sys.exit(1)

    workflow = ClosiraWorkflow()
    greeting = workflow.get_greeting()
    print_ivy(greeting)

    print(f"\n{DIM}Commands: type your message | 'summary' to end session | 'quit' to exit{RESET}\n")

    while True:
        try:
            user_input = input(f"{GREEN}You: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEnding session...")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "bye"]:
            print(f"\n{DIM}Generating session summary before exit...{RESET}")
            summary = workflow.generate_session_summary()
            print_summary(summary)
            break

        if user_input.lower() == "summary":
            print(f"\n{DIM}Generating session summary...{RESET}")
            summary = workflow.generate_session_summary()
            print_summary(summary)
            continue

        result = workflow.process_message(user_input)

        print_ivy(result["message"])
        print_meta(result.get("confidence"), result.get("sop_gap"))

        if result["escalated"] and result["escalation_reason"]:
            print_escalation(result["escalation_reason"])

        if result.get("show_qualification"):
            print(f"{DIM}   [Lead Qualification — Question {workflow.session.qualification_questions_asked}/{3}]{RESET}")


if __name__ == "__main__":
    main()
