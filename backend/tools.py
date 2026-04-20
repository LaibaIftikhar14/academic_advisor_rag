# backend/tools.py
# ─────────────────────────────────────────────
# Tools Module — 3 additional callable tools
#
# Tools:
#   1. Calculator    — math expressions
#   2. Study Planner — personalized schedule
#   3. GPA Calculator — grade point average
#
# WHY TOOLS:
#   Some questions need computation, not conversation.
#   Tools give the LLM the ability to perform actions
#   and return accurate results.
#
# HOW TOOL CALLING WORKS:
#   1. LLM detects tool needed from user message
#   2. Tool is called with extracted arguments
#   3. Result injected back into LLM prompt
#   4. LLM formulates natural language response
# ─────────────────────────────────────────────

import re
import json
import asyncio
from datetime import datetime, timedelta
from sympy import sympify, SympifyError


# ── TOOL REGISTRY ─────────────────────────────
# Each tool has: name, description, keywords
# Keywords help detect when to call the tool
# ─────────────────────────────────────────────

TOOLS = {
    "calculator": {
        "name":        "calculator",
        "description": "Evaluates mathematical expressions. Use for any math calculation.",
        "keywords":    ["calculate", "compute", "what is", "solve", "math",
                        "plus", "minus", "times", "divided", "sqrt", "square root",
                        "percent", "%", "+", "-", "*", "/", "="]
    },
    "study_planner": {
        "name":        "study_planner",
        "description": "Creates a personalized study schedule based on subjects and days available.",
        "keywords":    ["study plan", "study schedule", "plan my study", "schedule",
                        "how should i study", "organize my study", "study timetable",
                        "exam schedule", "revision plan", "study routine"]
    },
    "gpa_calculator": {
        "name":        "gpa_calculator",
        "description": "Calculates GPA from course grades and credit hours.",
        "keywords":    ["gpa", "grade point", "calculate my gpa", "what is my gpa",
                        "cgpa", "grades", "calculate grade", "my average"]
    }
}


# ── TOOL DETECTION ────────────────────────────

def detect_tool(user_message: str) -> str | None:
    """
    Detects which tool to call.
    Order matters — check specific tools FIRST.
    """
    msg_lower = user_message.lower()

    # ── Check study planner FIRST (most specific) ──
    study_keywords = [
        "study plan", "study schedule", "plan my study",
        "study timetable", "revision plan", "study routine",
        "how should i study", "organize my study", "exam schedule"
    ]
    if any(kw in msg_lower for kw in study_keywords):
        print("Tool detected: study_planner")
        return "study_planner"

    # ── Check GPA calculator SECOND ──
    gpa_keywords = [
        "gpa", "grade point", "calculate my gpa",
        "what is my gpa", "cgpa", "calculate grade"
    ]
    if any(kw in msg_lower for kw in gpa_keywords):
        print("Tool detected: gpa_calculator")
        return "gpa_calculator"

    # ── Check calculator LAST (most generic) ──
    calc_keywords = [
        "calculate", "compute", "sqrt", "square root",
        "what is 2", "what is 3", "what is 4", "what is 5",
        "solve", "evaluate", "plus", "minus", "times",
        "divided by", "percent of", "% of"
    ]
    if any(kw in msg_lower for kw in calc_keywords):
        print("Tool detected: calculator")
        return "calculator"

    return None


# ── TOOL 1: CALCULATOR ────────────────────────

def run_calculator(user_message: str) -> str:
    """
    Extracts and evaluates mathematical expressions
    from user messages.

    Uses sympy for safe, accurate evaluation.
    WHY SYMPY: Handles complex math safely without eval()
    eval() is dangerous — sympy is safe and powerful.

    Examples:
    "what is 15% of 200?" → "15% of 200 = 30.0"
    "calculate sqrt(144)" → "sqrt(144) = 12"
    "2^10"                → "2^10 = 1024"
    """
    msg = user_message.lower()

    # Handle percentage calculations specially
    # Pattern: "X% of Y"
    percent_match = re.search(
        r'(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)', msg
    )
    if percent_match:
        percent = float(percent_match.group(1))
        total   = float(percent_match.group(2))
        result  = (percent / 100) * total
        return f"{percent}% of {total} = {result}"

    # Extract mathematical expression from message
    # Remove common words to isolate the math
    expression = msg
    for word in ["calculate", "compute", "what is", "solve",
                 "find", "evaluate", "what's", "equals"]:
        expression = expression.replace(word, "")

    # Clean up the expression
    expression = expression.strip()
    expression = re.sub(r'[^0-9+\-*/().^ %sqrtlogsincotan]', ' ', expression)
    expression = expression.strip()

    if not expression:
        return "Please provide a mathematical expression to calculate."

    try:
        # Use sympy for safe evaluation
        result = sympify(expression)
        result_float = float(result)

        # Return clean integer if possible
        if result_float == int(result_float):
            return f"Result: {int(result_float)}"
        else:
            return f"Result: {round(result_float, 4)}"

    except (SympifyError, Exception) as e:
        return f"I could not evaluate that expression. Please write it clearly, e.g. '2 + 2', 'sqrt(16)', '15% of 200'."


# ── TOOL 2: STUDY PLANNER ─────────────────────

def run_study_planner(user_message: str) -> str:
    """
    Creates a personalized study schedule.

    Extracts from message:
    - Subjects to study
    - Days available
    - Exam date (if mentioned)

    Returns a formatted weekly study plan.

    WHY THIS TOOL:
    Students often ask "how should I plan my study?"
    A structured plan is more useful than generic advice.
    """
    msg_lower = user_message.lower()

    # ── Extract subjects ──
    # Common subjects in CS/university
    subject_keywords = {
        "Mathematics":      ["math", "calculus", "algebra", "statistics", "maths"],
        "Programming":      ["programming", "coding", "python", "java", "cs"],
        "Data Structures":  ["data structures", "algorithms", "dsa"],
        "Networks":         ["networks", "networking", "tcp"],
        "Databases":        ["database", "sql", "db"],
        "AI/ML":            ["ai", "machine learning", "ml", "artificial intelligence"],
        "Physics":          ["physics"],
        "Chemistry":        ["chemistry"],
        "English":          ["english", "writing", "essay"],
        "Economics":        ["economics", "finance", "business"]
    }

    subjects = []
    for subject, keywords in subject_keywords.items():
        if any(kw in msg_lower for kw in keywords):
            subjects.append(subject)

    # Default subjects if none detected
    if not subjects:
        subjects = ["Subject 1", "Subject 2", "Subject 3"]

    # ── Extract number of days ──
    days_match = re.search(r'(\d+)\s*days?', msg_lower)
    num_days   = int(days_match.group(1)) if days_match else 7

    # Cap at reasonable range
    num_days = max(1, min(num_days, 14))

    # ── Extract exam urgency ──
    urgent = any(word in msg_lower for word in [
        "tomorrow", "tonight", "today", "urgent", "asap"
    ])

    # ── Generate schedule ──
    days_of_week = ["Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday", "Sunday"]

    schedule_lines = []
    schedule_lines.append(f"📅 Study Plan ({num_days} days | {len(subjects)} subjects)\n")
    schedule_lines.append("=" * 40)

    if urgent:
        # Emergency cramming schedule
        schedule_lines.append("\n⚠️  URGENT MODE — Intensive Schedule:\n")
        for i, subject in enumerate(subjects):
            schedule_lines.append(f"• {subject}: 2-3 hours — focus on key topics only")
        schedule_lines.append("\n💡 Tips for urgent study:")
        schedule_lines.append("  - Use active recall, not re-reading")
        schedule_lines.append("  - Focus on past paper questions")
        schedule_lines.append("  - Get 6+ hours sleep — it matters more than extra study")
    else:
        # Regular schedule
        sessions_per_day = max(1, len(subjects))
        session_duration = 90 // sessions_per_day  # minutes per session

        for day_num in range(num_days):
            day_name = days_of_week[day_num % 7]
            schedule_lines.append(f"\n📌 {day_name}:")

            # Rotate subjects across days
            for i, subject in enumerate(subjects):
                if (day_num + i) % 3 != 0:  # rest day for each subject every 3rd day
                    schedule_lines.append(
                        f"  • {subject}: {session_duration} min"
                        f" ({['Morning', 'Afternoon', 'Evening'][i % 3]})"
                    )

            # Add review on last day
            if day_num == num_days - 1:
                schedule_lines.append(f"  • Review ALL subjects: 60 min")

        schedule_lines.append("\n" + "=" * 40)
        schedule_lines.append("💡 Study Tips:")
        schedule_lines.append("  - Use Pomodoro: 25 min study, 5 min break")
        schedule_lines.append("  - Active recall > passive reading")
        schedule_lines.append("  - Sleep 7-8 hours every night")

    return "\n".join(schedule_lines)


# ── TOOL 3: GPA CALCULATOR ────────────────────

def run_gpa_calculator(user_message: str) -> str:
    """
    Calculates GPA from grades mentioned in message.

    Supports:
    - Letter grades: A, B+, C, etc.
    - Percentage grades: 85%, 72%, etc.
    - Credit hours if mentioned

    WHY THIS TOOL:
    GPA calculation confuses many students.
    An accurate, instant calculation builds trust.

    Grade scale used:
    A+ = 4.0, A = 4.0, A- = 3.7
    B+ = 3.3, B = 3.0, B- = 2.7
    C+ = 2.3, C = 2.0, C- = 1.7
    D = 1.0, F = 0.0
    """

    # ── Grade point mapping ──
    grade_points = {
        "a+": 4.0, "a": 4.0, "a-": 3.7,
        "b+": 3.3, "b": 3.0, "b-": 2.7,
        "c+": 2.3, "c": 2.0, "c-": 1.7,
        "d+": 1.3, "d": 1.0, "d-": 0.7,
        "f":  0.0
    }

    msg_lower = user_message.lower()

    # ── Extract letter grades ──
    letter_pattern = re.findall(r'\b([abcdf][+-]?)\b', msg_lower)
    letter_grades  = [g for g in letter_pattern if g in grade_points]

    # ── Extract percentage grades ──
    percent_pattern = re.findall(r'(\d{2,3})\s*%?', user_message)
    percent_grades  = [int(p) for p in percent_pattern if 0 <= int(p) <= 100]

    # Convert percentages to letter grades
    def percent_to_points(pct: int) -> float:
        if pct >= 95: return 4.0
        if pct >= 90: return 4.0
        if pct >= 85: return 3.7
        if pct >= 80: return 3.3
        if pct >= 75: return 3.0
        if pct >= 70: return 2.7
        if pct >= 65: return 2.3
        if pct >= 60: return 2.0
        if pct >= 55: return 1.7
        if pct >= 50: return 1.0
        return 0.0

    # ── Calculate GPA ──
    all_points = []

    if letter_grades:
        for grade in letter_grades:
            all_points.append(grade_points[grade])

    if percent_grades and not letter_grades:
        for pct in percent_grades:
            all_points.append(percent_to_points(pct))

    if not all_points:
        return (
            "Please provide your grades to calculate GPA.\n"
            "Example: 'I got A, B+, A-, C in my courses'\n"
            "Or: 'I got 85%, 72%, 90%, 68%'"
        )

    gpa = sum(all_points) / len(all_points)
    gpa = round(gpa, 2)

    # ── Format result ──
    if gpa >= 3.7:
        standing = "Excellent — Dean's List eligible!"
        emoji    = "🏆"
    elif gpa >= 3.3:
        standing = "Very Good"
        emoji    = "⭐"
    elif gpa >= 3.0:
        standing = "Good"
        emoji    = "✅"
    elif gpa >= 2.0:
        standing = "Satisfactory — above minimum requirement"
        emoji    = "📚"
    else:
        standing = "Below minimum — please see your academic advisor"
        emoji    = "⚠️"

    lines = [
        f"{emoji} GPA Calculation Result",
        f"{'=' * 30}",
        f"Grades entered: {len(all_points)} courses",
    ]

    if letter_grades:
        lines.append(f"Grades: {', '.join(letter_grades).upper()}")
    if percent_grades and not letter_grades:
        lines.append(f"Grades: {', '.join(str(p)+'%' for p in percent_grades)}")

    lines.extend([
        f"{'=' * 30}",
        f"📊 Your GPA: {gpa} / 4.0",
        f"📈 Standing: {standing}",
        f"{'=' * 30}",
        f"💡 Need to improve? Visit your academic advisor",
        f"   or ask me for study strategies!"
    ])

    return "\n".join(lines)


# ── MAIN TOOL RUNNER ──────────────────────────

async def run_tool(tool_name: str, user_message: str) -> str:
    """
    Runs the specified tool and returns result.
    Async so it does not block the main conversation.

    WHY ASYNC:
    Tools could be slow (API calls, computation).
    Async ensures other users are not blocked.
    """
    try:
        if tool_name == "calculator":
            # Run in executor to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, run_calculator, user_message
            )
            return result

        elif tool_name == "study_planner":
            result = await asyncio.get_event_loop().run_in_executor(
                None, run_study_planner, user_message
            )
            return result

        elif tool_name == "gpa_calculator":
            result = await asyncio.get_event_loop().run_in_executor(
                None, run_gpa_calculator, user_message
            )
            return result

        else:
            return f"Unknown tool: {tool_name}"

    except Exception as e:
        print(f"Tool error ({tool_name}): {e}")
        return f"The {tool_name} tool encountered an error. Please try again."