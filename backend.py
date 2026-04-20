import os
import json
import re
from google import genai
from dotenv import load_dotenv
from database import get_connection

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# =========================
# AI
# =========================
def generate_question(role, difficulty, language, previous_questions):

    prompt = f"""
Generate ONE interview question.

Role: {role}
Difficulty: {difficulty}
Language: {language}

Avoid repetition:
{chr(10).join(previous_questions)}

Return only question.
"""

    res = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    return res.text.strip()


def evaluate_answer(question, answer):

    prompt = f"""
Return JSON only.

Q: {question}
A: {answer}

{{
"score": 0-10,
"strengths": "",
"weaknesses": "",
"ideal_answer": ""
}}
"""

    res = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    match = re.search(r"\{.*\}", res.text, re.DOTALL)

    if match:
        return json.loads(match.group())

    return {
        "score": 0,
        "strengths": "error",
        "weaknesses": "",
        "ideal_answer": ""
    }


# =========================
# DB FUNCTIONS
# =========================
def save_interview(user_id, role, difficulty, language):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO interviews (user_id, role, difficulty, language)
    VALUES (?, ?, ?, ?)
    """, (user_id, role, difficulty, language))

    conn.commit()
    iid = cur.lastrowid
    conn.close()
    return iid


def save_question(interview_id, question):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO questions (interview_id, question_text)
    VALUES (?, ?)
    """, (interview_id, question))

    conn.commit()
    qid = cur.lastrowid
    conn.close()
    return qid


def save_answer(question_id, answer):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO answers (question_id, answer_text)
    VALUES (?, ?)
    """, (question_id, answer))

    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def save_score(answer_id, eval):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO scores (answer_id, score, strengths, weaknesses, ideal_answer)
    VALUES (?, ?, ?, ?, ?)
    """, (
        answer_id,
        eval["score"],
        eval["strengths"],
        eval["weaknesses"],
        eval["ideal_answer"]
    ))

    conn.commit()
    conn.close()


# =========================
# FLOW
# =========================
def start_interview(user_id, role, difficulty, language):

    interview_id = save_interview(user_id, role, difficulty, language)

    return {
        "interview_id": interview_id,
        "user_id": user_id,
        "role": role,
        "difficulty": difficulty,
        "language": language,
        "questions": [],
        "current_index": 0,
        "max_questions": 2,
        "completed": False,
        "last_answered": False
    }


def next_question(session):

    if session["current_index"] >= session["max_questions"]:
        return None

    q = generate_question(
        session["role"],
        session["difficulty"],
        session["language"],
        [x["text"] for x in session["questions"]]
    )

    qid = save_question(session["interview_id"], q)

    session["questions"].append({
        "id": qid,
        "text": q
    })

    session["current_index"] += 1
    session["last_answered"] = False

    return q


def submit_answer(session, answer):

    if session["completed"]:
        return {"score": 0, "strengths": "Completed", "weaknesses": "", "ideal_answer": ""}

    if session["last_answered"]:
        return {"score": 0, "strengths": "Already answered", "weaknesses": "", "ideal_answer": ""}

    q = session["questions"][-1]

    eval = evaluate_answer(q["text"], answer)

    aid = save_answer(q["id"], answer)
    save_score(aid, eval)

    session["last_answered"] = True

    if session["current_index"] >= session["max_questions"]:
        session["completed"] = True

    return eval


def get_results(interview_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        q.question_text,
        a.answer_text,
        s.score,
        s.strengths,
        s.weaknesses,
        s.ideal_answer
    FROM questions q
    JOIN answers a ON q.id = a.question_id
    JOIN scores s ON a.id = s.answer_id
    WHERE q.interview_id = ?
    """, (interview_id,))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {
            "average_score": 0,
            "details": []
        }

    total = sum([r[2] for r in rows])
    avg = total / len(rows)

    return {
        "average_score": avg,
        "details": rows
    }