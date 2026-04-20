# backend/session.py
# ─────────────────────────────────────────────
# Session Manager — stores conversation memory
# for each connected user independently.
#
# WHY A DICT?
# Simple, fast, zero dependencies. For production
# you'd swap this for Redis — same interface.
# ─────────────────────────────────────────────

from typing import Dict, List
from config import SYSTEM_PROMPT

# In-memory store: { session_id: [messages] }
_sessions: Dict[str, List[dict]] = {}


def get_or_create_session(session_id: str) -> List[dict]:
    """
    Returns the message history for a session.
    Creates a fresh session with the system prompt if it doesn't exist.
    """
    if session_id not in _sessions:
        # Every new session starts with the system prompt.
        # This is ALWAYS the first message — it never gets trimmed.
        _sessions[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    return _sessions[session_id]


def add_message(session_id: str, role: str, content: str) -> None:
    """
    Appends a single message to a session's history.
    role must be: "user" or "assistant"
    """
    history = get_or_create_session(session_id)
    history.append({"role": role, "content": content})


def clear_session(session_id: str) -> None:
    """
    Resets a session — used when user clicks 'New Chat'.
    Re-inserts system prompt so the AI still knows its role.
    """
    _sessions[session_id] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]


def get_session_count() -> int:
    """Returns number of active sessions — useful for monitoring."""
    return len(_sessions)