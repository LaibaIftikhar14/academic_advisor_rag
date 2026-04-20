# backend/conversation.py
# ─────────────────────────────────────────────
# Conversation Manager — FINAL VERSION (Assignment 4)
#
# New additions:
#   1. RAG — retrieves relevant document chunks
#   2. CRM — remembers student info across sessions
#   3. Tools — calculator, study planner, GPA calc
#
# Existing features kept:
#   - Policy enforcement (ethics + wellbeing)
#   - Academic scope check (LLM classifier)
#   - Memory summarization
#   - Sliding window memory
#   - Closing detection
# ─────────────────────────────────────────────

import asyncio
import httpx
from session import get_or_create_session, add_message
from config import MAX_HISTORY_MESSAGES, OLLAMA_URL, MODEL_NAME
from rag import retrieve, format_context
from crm import get_or_create_user, format_user_context, extract_and_update_user_info
from tools import detect_tool, run_tool
from typing import AsyncGenerator


# ── POLICY KEYWORDS ───────────────────────────

OFF_TOPIC_KEYWORDS = [
    "write my assignment", "do my homework",
    "write my essay", "complete my project for me",
    "write my code", "give me the answers to"
]

WELLBEING_KEYWORDS = [
    "give up", "can't do this", "want to drop out",
    "feeling hopeless", "hate myself", "i'm a failure",
    "no point", "end it all"
]

CLOSING_KEYWORDS = [
    "bye", "goodbye", "thank you", "thanks", "that's all",
    "thats all", "i'm done", "im done", "no more questions",
    "that's everything", "thats everything", "see you",
    "i'm good now", "im good now", "all done"
]

CLOSING_RESPONSE = (
    "It was great helping you today! "
    "Remember, academic success is a journey — "
    "take it one step at a time. "
    "Best of luck with your studies! "
    "Come back anytime you need guidance. Goodbye!"
)


# ── LLM HELPER ────────────────────────────────

async def ask_llm(prompt: str) -> str:
    """Sends a single prompt to LLM, returns complete response."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model":    MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream":   False
                }
            )
            data = response.json()
            return data.get("message", {}).get("content", "").strip()
    except Exception as e:
        print(f"LLM helper error: {e}")
        return ""


# ── SCOPE CLASSIFIER ──────────────────────────

SCOPE_CLASSIFIER_PROMPT = """Is this message related to university or academic life?

Message: "{message}"

Academic topics: studying, exams, courses, grades, university, semester, planning, assignments, deadlines, professors, stress about school, career after university, GPA, math calculations, study schedules.

Non-academic topics: weather, sports, cooking, politics, entertainment, relationships, general knowledge unrelated to studies.

Reply with ONE word only: YES or NO"""


async def is_academic(user_message: str) -> bool:
    """Uses LLM to classify if message is academic."""
    if len(user_message.split()) <= 3:
        return True
    prompt = SCOPE_CLASSIFIER_PROMPT.format(message=user_message)
    result = await ask_llm(prompt)
    print(f"Scope check: '{user_message[:50]}' → {result}")
    if result.strip().upper().startswith("NO"):
        return False
    return True


# ── SUMMARIZER ────────────────────────────────

SUMMARIZATION_PROMPT = """You are an academic memory manager.

Extract ONLY the academically relevant facts from this conversation turn.

Extract if present:
- Student name, year, major
- Specific academic problems mentioned
- Courses or subjects mentioned
- Advice that was given

Student said: "{user_message}"
AI responded: "{ai_response}"

Write ONE short sentence with only the academic facts.
If nothing academic was said, write exactly: NOTHING"""


async def summarize_turn(user_message: str, ai_response: str) -> str:
    """Extracts academic facts from one conversation turn."""
    prompt = SUMMARIZATION_PROMPT.format(
        user_message=user_message,
        ai_response=ai_response[:300]
    )
    summary = await ask_llm(prompt)
    if not summary or "NOTHING" in summary.upper():
        return ""
    print(f"Memory saved: {summary}")
    return summary


# ── POLICY CHECKS ─────────────────────────────

def check_policy(user_message: str) -> str | None:
    """Keyword-based safety policy check."""
    msg_lower = user_message.lower()

    for phrase in OFF_TOPIC_KEYWORDS:
        if phrase in msg_lower:
            return (
                "I'm not able to complete academic work for you — "
                "that wouldn't actually help you learn or succeed. "
                "But I'd love to help you break the task down, "
                "build a plan, or talk through the concepts. "
                "Where would you like to start?"
            )

    for phrase in WELLBEING_KEYWORDS:
        if phrase in msg_lower:
            return (
                "I hear you, and what you're feeling is real and valid. "
                "Please know you're not alone in this. "
                "I'd strongly encourage you to reach out to your "
                "university counseling or student support services. "
                "When you're ready, I'm here to help you make a "
                "manageable plan, one small step at a time."
            )

    return None


def check_closing(user_message: str) -> bool:
    """Returns True if user wants to end conversation."""
    msg_lower = user_message.lower()
    return any(phrase in msg_lower for phrase in CLOSING_KEYWORDS)


def trim_history(history: list) -> list:
    """Sliding window memory trim."""
    system_prompt = history[0]
    conversation  = history[1:]
    if len(conversation) > MAX_HISTORY_MESSAGES:
        conversation = conversation[-MAX_HISTORY_MESSAGES:]
    return [system_prompt] + conversation


# ── PROMPT BUILDER ────────────────────────────

def build_enhanced_prompt(
    base_history:   list,
    rag_context:    str,
    user_context:   str,
    tool_result:    str
) -> list:
    """
    Builds the final prompt by injecting:
    - RAG context (relevant document chunks)
    - CRM user profile
    - Tool results

    WHY INJECT INTO SYSTEM PROMPT:
    The system message is always first and most
    authoritative — LLM pays most attention to it.

    Structure:
    [Enhanced system prompt with RAG + CRM + Tool]
    [Conversation history]
    [Current user message]
    """
    enhanced_history = list(base_history)

    # Build injection content
    injections = []

    if user_context:
        injections.append(f"STUDENT PROFILE:\n{user_context}")

    if rag_context:
        injections.append(
            f"RELEVANT UNIVERSITY INFORMATION:\n{rag_context}\n"
            f"Use this information to ground your response. "
            f"Reference it naturally when relevant."
        )

    if tool_result:
        injections.append(
            f"TOOL RESULT:\n{tool_result}\n"
            f"Present this result to the student clearly and helpfully."
        )

    if injections:
        injection_text = "\n\n".join(injections)
        # Inject after system prompt
        enhanced_history.insert(1, {
            "role":    "system",
            "content": injection_text
        })

    return enhanced_history


# ── MAIN ENTRY POINT ──────────────────────────

async def handle_turn(
    session_id:   str,
    user_message: str,
    llm_stream_fn
) -> AsyncGenerator[str, None]:
    """
    Full conversation turn pipeline — Assignment 4:

    1.  Policy check        (keyword — safety)
    2.  Closing check       (keyword)
    3.  CRM update          (extract user info silently)
    4.  Tool detection      (calculator/planner/GPA)
    5.  Academic scope check (LLM classifier)
    6.  RAG retrieval       (find relevant docs)
    7.  Build enhanced prompt (inject RAG + CRM + tools)
    8.  Stream LLM response
    9.  Summarize + save to memory
    """

    # ── STEP 1: Safety policy check ──
    policy_response = check_policy(user_message)
    if policy_response:
        add_message(session_id, "user", user_message)
        add_message(session_id, "assistant", policy_response)
        for word in policy_response.split(" "):
            yield word + " "
        return

    # ── STEP 2: Closing check ──
    if check_closing(user_message):
        add_message(session_id, "user", user_message)
        add_message(session_id, "assistant", CLOSING_RESPONSE)
        for word in CLOSING_RESPONSE.split(" "):
            yield word + " "
        yield "__CONVERSATION_ENDED__"
        return

    # ── STEP 3: CRM — extract user info silently ──
    # Update CRM with any info mentioned in message
    extract_and_update_user_info(session_id, user_message)
    user_data    = get_or_create_user(session_id)
    user_context = format_user_context(user_data)
    if user_context:
        print(f"CRM context: {user_context}")

    # ── STEP 4: Tool detection ──
    tool_name   = detect_tool(user_message)
    tool_result = ""
    if tool_name:
        try:
            tool_result = await asyncio.wait_for(
                run_tool(tool_name, user_message),
                timeout=10.0
            )
            print(f"Tool result: {tool_result[:100]}")
        except asyncio.TimeoutError:
            print("Tool timed out")
            tool_result = ""

    # ── STEP 5: Academic scope check ──
    try:
        academic = await asyncio.wait_for(
            is_academic(user_message),
            timeout=8.0
        )
    except asyncio.TimeoutError:
        academic = True

    if not academic:
        refusal = (
            "I'm here specifically to help with academic topics — "
            "things like courses, exams, study strategies, and "
            "university life. I'm not able to help with that topic. "
            "Is there anything academic I can assist you with?"
        )
        for word in refusal.split(" "):
            yield word + " "
        return

    # ── STEP 6: RAG retrieval ──
    rag_chunks  = []
    rag_context = ""
    try:
        rag_chunks = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, retrieve, user_message
            ),
            timeout=5.0
        )
        rag_context = format_context(rag_chunks)
        if rag_context:
            print(f"RAG: retrieved {len(rag_chunks)} chunks")
    except asyncio.TimeoutError:
        print("RAG timed out — proceeding without context")

    # ── STEP 7: Build enhanced prompt ──
    add_message(session_id, "user", user_message)
    raw_history     = get_or_create_session(session_id)
    trimmed_history = trim_history(raw_history)

    enhanced_history = build_enhanced_prompt(
        base_history = trimmed_history,
        rag_context  = rag_context,
        user_context = user_context,
        tool_result  = tool_result
    )

    # ── STEP 8: Stream LLM response ──
    full_reply = ""
    async for token in llm_stream_fn(enhanced_history):
        full_reply += token
        yield token

    # ── STEP 9: Summarize + save to memory ──
    try:
        summary = await asyncio.wait_for(
            summarize_turn(user_message, full_reply),
            timeout=8.0
        )
    except asyncio.TimeoutError:
        summary = ""

    if summary:
        add_message(session_id, "assistant", f"[Memory: {summary}]")
    else:
        add_message(session_id, "assistant", full_reply)