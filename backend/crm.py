# backend/crm.py
# ─────────────────────────────────────────────
# CRM Tool — Customer Relationship Management
#
# What it does:
#   Remembers student information across sessions
#   Stores: name, year, major, concerns, history
#   Persists to JSON file so data survives restarts
#
# WHY CRM:
#   Without CRM, every conversation starts fresh.
#   With CRM, returning students are greeted by name
#   and the AI remembers their previous concerns.
#
# Storage: JSON file (simple, no database needed)
# ─────────────────────────────────────────────

import json
import os
from datetime import datetime
from pathlib import Path

# ── CONFIG ────────────────────────────────────
CRM_FILE = "../crm_data.json"   # persistent storage file


# ── LOAD / SAVE ───────────────────────────────

def _load_crm() -> dict:
    """Loads CRM data from JSON file."""
    path = Path(CRM_FILE)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_crm(data: dict) -> None:
    """Saves CRM data to JSON file."""
    Path(CRM_FILE).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


# ── CRM OPERATIONS ────────────────────────────

def get_user(user_id: str) -> dict | None:
    """
    Retrieves stored information for a user.

    Returns dict with user info or None if not found.

    WHY: When a returning student connects, we can
    greet them by name and recall their situation.

    Example return:
    {
        "name": "Sara",
        "year": "2nd year",
        "major": "Computer Science",
        "concerns": ["exam stress", "workload"],
        "last_seen": "2026-04-19",
        "interaction_count": 3
    }
    """
    data = _load_crm()
    return data.get(user_id, None)


def create_user(user_id: str, name: str = "", year: str = "", major: str = "") -> dict:
    """
    Creates a new user record in the CRM.

    Called when a new student starts a conversation
    and shares their information.
    """
    data = _load_crm()

    user = {
        "name":              name,
        "year":              year,
        "major":             major,
        "concerns":          [],
        "advice_given":      [],
        "interaction_count": 1,
        "first_seen":        datetime.now().strftime("%Y-%m-%d"),
        "last_seen":         datetime.now().strftime("%Y-%m-%d")
    }

    data[user_id] = user
    _save_crm(data)
    print(f"CRM: Created user {user_id} — {name}")
    return user


def update_user(user_id: str, field: str, value) -> bool:
    """
    Updates a specific field for a user.

    Fields that can be updated:
    - name, year, major (strings)
    - concerns, advice_given (lists — value gets appended)

    WHY: As conversation progresses, we learn more
    about the student and update their profile.

    Returns True if successful, False if user not found.
    """
    data = _load_crm()

    if user_id not in data:
        return False

    # List fields get appended to, not replaced
    if field in ["concerns", "advice_given"]:
        if value not in data[user_id][field]:
            data[user_id][field].append(value)
    else:
        data[user_id][field] = value

    # Always update last seen
    data[user_id]["last_seen"] = datetime.now().strftime("%Y-%m-%d")
    data[user_id]["interaction_count"] = data[user_id].get("interaction_count", 0) + 1

    _save_crm(data)
    print(f"CRM: Updated {user_id} — {field} = {value}")
    return True


def get_or_create_user(user_id: str) -> dict:
    """
    Returns existing user or creates a blank new one.
    Used at the start of every session.
    """
    user = get_user(user_id)
    if user:
        # Update last seen for returning user
        data = _load_crm()
        data[user_id]["last_seen"] = datetime.now().strftime("%Y-%m-%d")
        _save_crm(data)
        print(f"CRM: Returning user {user_id} — {user.get('name', 'Unknown')}")
        return user
    else:
        return create_user(user_id)


def format_user_context(user: dict) -> str:
    """
    Formats user CRM data into a string to inject
    into the LLM system prompt.

    WHY: The LLM needs to know about the student
    to provide personalized responses.

    Example output:
    "Student profile: Name: Sara | Year: 2nd year |
     Major: CS | Previous concerns: exam stress"
    """
    if not user:
        return ""

    parts = []

    if user.get("name"):
        parts.append(f"Name: {user['name']}")
    if user.get("year"):
        parts.append(f"Year: {user['year']}")
    if user.get("major"):
        parts.append(f"Major: {user['major']}")
    if user.get("concerns"):
        concerns = ", ".join(user["concerns"][-3:])  # last 3 concerns
        parts.append(f"Previous concerns: {concerns}")
    if user.get("interaction_count", 0) > 1:
        parts.append(f"Returning student (visit #{user['interaction_count']})")

    if not parts:
        return ""

    return "Student profile: " + " | ".join(parts)


def extract_and_update_user_info(user_id: str, user_message: str) -> None:
    """
    Automatically extracts user info from messages
    and updates CRM without asking the LLM.

    Detects patterns like:
    - "I'm Sara" → updates name
    - "2nd year" → updates year
    - "CS major" or "studying CS" → updates major

    WHY: We want to silently learn from the conversation
    without making the student fill out a form.
    """
    msg_lower = user_message.lower()

    # Extract name patterns: "I'm Sara", "my name is Sara"
    import re
    name_patterns = [
        r"i['']m ([A-Z][a-z]+)",
        r"my name is ([A-Z][a-z]+)",
        r"this is ([A-Z][a-z]+)",
        r"call me ([A-Z][a-z]+)"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, user_message)
        if match:
            name = match.group(1)
            update_user(user_id, "name", name)
            break

    # Extract year patterns: "2nd year", "first year", "junior"
    year_patterns = {
        "1st year": ["1st year", "first year", "freshman"],
        "2nd year": ["2nd year", "second year", "sophomore"],
        "3rd year": ["3rd year", "third year", "junior"],
        "4th year": ["4th year", "fourth year", "senior"],
        "graduate": ["graduate", "masters", "phd", "postgrad"]
    }
    for year, keywords in year_patterns.items():
        if any(kw in msg_lower for kw in keywords):
            update_user(user_id, "year", year)
            break

    # Extract major patterns: "CS major", "studying computer science"
    major_patterns = {
        "Computer Science": ["computer science", "cs major", "software engineering"],
        "Mathematics":      ["mathematics", "math major", "maths"],
        "Engineering":      ["engineering", "electrical", "mechanical", "civil"],
        "Business":         ["business", "mba", "management", "finance"],
        "Medicine":         ["medicine", "medical", "pre-med", "mbbs"],
        "Arts":             ["arts", "humanities", "literature", "history"]
    }
    for major, keywords in major_patterns.items():
        if any(kw in msg_lower for kw in keywords):
            update_user(user_id, "major", major)
            break

    # Extract concerns
    concern_keywords = {
        "exam stress":    ["exam stress", "exam anxiety", "nervous about exam"],
        "workload":       ["too much work", "overwhelmed", "overloaded"],
        "time management":["no time", "time management", "busy"],
        "grades":         ["failing", "bad grades", "gpa", "grade"],
        "career":         ["job", "career", "internship", "interview"],
        "mental health":  ["anxious", "depressed", "burnout", "stressed"]
    }
    for concern, keywords in concern_keywords.items():
        if any(kw in msg_lower for kw in keywords):
            update_user(user_id, "concerns", concern)