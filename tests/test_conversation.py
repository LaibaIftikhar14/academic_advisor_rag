# tests/test_conversation.py
# ─────────────────────────────────────────────
# Unit tests for the Conversation Manager.
# Run with: pytest tests/test_conversation.py -v
# ─────────────────────────────────────────────

import sys
import asyncio
import websockets
import json
import time
sys.path.insert(0, "backend")

from conversation import check_policy, trim_history
from config import SYSTEM_PROMPT, MAX_HISTORY_MESSAGES


# ── POLICY TESTS ──────────────────────────────

def test_clean_message_passes_policy():
    """Normal academic question should return None (no violation)."""
    result = check_policy("How should I study for my calculus exam?")
    assert result is None

def test_ethics_violation_caught():
    """Asking AI to write assignment should return canned response."""
    result = check_policy("Can you write my assignment for me?")
    assert result is not None
    assert "not able to complete academic work" in result

def test_wellbeing_trigger_caught():
    """Distress signals should return empathetic canned response."""
    result = check_policy("I just want to give up on everything")
    assert result is not None
    assert "counseling" in result.lower()

def test_case_insensitive_policy():
    """Policy check should work regardless of capitalisation."""
    result = check_policy("WRITE MY ESSAY please")
    assert result is not None


# ── MEMORY TRIM TESTS ─────────────────────────

def test_trim_keeps_system_prompt():
    """System prompt must always be first message after trimming."""
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    for i in range(30):
        history.append({"role": "user",      "content": f"msg {i}"})
        history.append({"role": "assistant", "content": f"reply {i}"})

    trimmed = trim_history(history)
    assert trimmed[0]["role"] == "system"

def test_trim_respects_max_length():
    """History after trim should not exceed MAX + 1 (system prompt)."""
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    for i in range(30):
        history.append({"role": "user",      "content": f"msg {i}"})
        history.append({"role": "assistant", "content": f"reply {i}"})

    trimmed = trim_history(history)
    assert len(trimmed) <= MAX_HISTORY_MESSAGES + 1

def test_short_history_not_trimmed():
    """Short history should be returned unchanged."""
    history = [
        {"role": "system",    "content": SYSTEM_PROMPT},
        {"role": "user",      "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]
    trimmed = trim_history(history)
    assert len(trimmed) == 3


# ── STRESS TESTS ──────────────────────────────

async def simulate_user(user_id: int):
    """Simulates a single student sending a message."""
    uri = "ws://localhost:8000/ws/chat"

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "message": f"Hi I am student {user_id}, how do I manage exam stress?"
        }))

        start = time.time()
        full_response = ""

        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if data["type"] == "token":
                full_response += data["content"]
            if data["type"] == "end":
                break

        elapsed = time.time() - start
        print(f"✅ User {user_id} → {elapsed:.2f}s | {len(full_response)} chars")


async def run_stress_test():
    """Launches 5 users simultaneously."""
    print("\n" + "=" * 50)
    print("  STRESS TEST — 5 Concurrent Users")
    print("=" * 50)

    start_total = time.time()

    await asyncio.gather(*[
        simulate_user(i) for i in range(1, 6)
    ])

    total = time.time() - start_total
    print(f"\n✅ All 5 users served successfully")
    print(f"⏱  Total time: {total:.2f}s")
    print("=" * 50)


def test_stress_concurrent_users():
    """
    Pytest-compatible stress test.
    Simulates 5 concurrent WebSocket users.
    Make sure backend is running before running this test!
    """
    asyncio.run(run_stress_test())