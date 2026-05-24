"""
Closira Web UI — Flask server
Serves the chat interface and API endpoints.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, session
from src.workflow import ClosiraWorkflow
from src.logging_utils import get_logger

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "closira-secret-2024")

# Ensure logging is configured early.
get_logger()

# In-memory session store (use Redis for production)
workflow_store: dict[str, ClosiraWorkflow] = {}


def get_workflow(session_id: str) -> ClosiraWorkflow:
    if session_id not in workflow_store:
        workflow_store[session_id] = ClosiraWorkflow()
    return workflow_store[session_id]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_session():
    """Start a new conversation session."""
    import uuid
    session_id = str(uuid.uuid4())
    session["sid"] = session_id
    workflow = get_workflow(session_id)
    greeting = workflow.get_greeting()
    return jsonify({
        "session_id": session_id,
        "message": greeting,
        "stage": "faq",
        "escalated": False,
        "confidence": 1.0,
        "sop_gap": None,
    })


@app.route("/api/message", methods=["POST"])
def send_message():
    """Process a user message."""
    data = request.get_json()
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id") or session.get("sid")

    if not session_id:
        return jsonify({"error": "No session found"}), 400
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    workflow = get_workflow(session_id)
    result = workflow.process_message(user_message)

    return jsonify(result)


@app.route("/api/summary", methods=["POST"])
def get_summary():
    """Generate and return conversation summary."""
    data = request.get_json()
    session_id = data.get("session_id") or session.get("sid")

    if not session_id or session_id not in workflow_store:
        return jsonify({"error": "No session found"}), 400

    workflow = workflow_store[session_id]
    summary = workflow.generate_session_summary()

    return jsonify({"summary": summary})


@app.route("/api/session", methods=["GET"])
def get_session_data():
    """Return full session data for debugging."""
    session_id = request.args.get("id") or session.get("sid")
    if not session_id or session_id not in workflow_store:
        return jsonify({"error": "No session found"}), 404
    return jsonify(workflow_store[session_id].get_session_data())


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("⚠️  Warning: GROQ_API_KEY not set. Set it before starting the server.")
    app.run(debug=True, port=5000)
