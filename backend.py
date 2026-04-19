import os
import json
import re
from google import genai
from dotenv import load_dotenv

# =========================
# INIT GEMINI CLIENT
# =========================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)


# =========================
# QUESTION GENERATION
# =========================
def generate_question(role, difficulty, language, previous_questions):
    prompt = f"""
You are a professional technical interviewer.

Generate ONE interview question for:
Role: {role}
Difficulty: {difficulty}
Language: {language}

Do NOT repeat these questions:
{chr(10).join(previous_questions)}

Return ONLY the question text.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        return response.text.strip()

    except Exception:
        return "Could not generate question."


# =========================
# ANSWER EVALUATION
# =========================
def evaluate_answer(question, answer):
    prompt = f"""
You are a strict technical interviewer.

Evaluate the answer and return ONLY valid JSON.

Question: {question}
Answer: {answer}

Return JSON in EXACT format:

{{
  "score": 0-10 number (can be decimal),
  "strengths": "string",
  "weaknesses": "string",
  "ideal_answer": "string"
}}

Rules:
- No extra text
- No markdown
- Only valid JSON
"""

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        text = response.text.strip()

        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        return {
            "score": 0,
            "strengths": "Parsing error",
            "weaknesses": "Invalid JSON from model",
            "ideal_answer": ""
        }

    except Exception as e:
        return {
            "score": 0,
            "strengths": "Error",
            "weaknesses": str(e),
            "ideal_answer": ""
        }


# =========================
# START INTERVIEW
# =========================
def start_interview(role, difficulty, language):
    return {
        "role": role,
        "difficulty": difficulty,
        "language": language,
        "questions": [],
        "answers": [],
        "scores": [],
        "current_index": 0,
        "max_questions": 2,
        "completed": False
    }


# =========================
# NEXT QUESTION
# =========================
def next_question(session):

    if session["current_index"] >= session["max_questions"]:
        session["completed"] = True
        return None

    question = generate_question(
        session["role"],
        session["difficulty"],
        session["language"],
        session["questions"]
    )

    session["questions"].append(question)
    session["current_index"] += 1

    return question


# =========================
# SUBMIT ANSWER
# =========================
def submit_answer(session, answer):

    if session.get("completed"):
        return {
            "score": 0,
            "strengths": "Interview completed",
            "weaknesses": "",
            "ideal_answer": ""
        }

    question = session["questions"][-1]
    evaluation = evaluate_answer(question, answer)

    session["answers"].append(answer)
    session["scores"].append(evaluation.get("score", 0))

    return evaluation


# =========================
# RESULTS
# =========================
def get_results(session):

    scores = session.get("scores", [])
    avg = sum(scores) / len(scores) if scores else 0

    return {
        "average_score": avg,
        "total_questions": len(session.get("questions", [])),
        "scores": scores
    }