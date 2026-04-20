import streamlit as st
from backend import (
    start_interview,
    next_question,
    submit_answer,
    get_results
)
from database import init_db, create_user
init_db()

ADMIN_PASSWORD = "Roy@50521"  # change this
st.sidebar.title("🔐 Admin Panel")

admin_key = st.sidebar.text_input("Enter Admin Password", type="password")

is_admin = (admin_key == ADMIN_PASSWORD)

st.title("🚀 BD JOB INTERVIEW")
st.subheader("Bangladesh Interview Platform")
st.divider()


# =========================
# SESSION STATE
# =========================
if "session" not in st.session_state:
    st.session_state.session = None

if "current_question" not in st.session_state:
    st.session_state.current_question = None


# =========================
# USER INPUT
# =========================
username = st.text_input("Enter your username")


# =========================
# SETUP
# =========================
role = st.selectbox(
    "Select Role",
    [
        "AI Engineer",
        "Machine Learning Engineer",
        "Data Scientist",
        "Data Analyst",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "DevOps Engineer",
        "Software Engineer",
        "Mobile App Developer"
    ],
    accept_new_options=True
)

difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
language = st.selectbox("Language", ["Bangla", "English"])


# =========================
# START INTERVIEW
# =========================
if st.button("Start Interview"):

    if not username.strip():
        st.warning("Please enter username first!")
        st.stop()

    user_id = create_user(username)

    st.session_state.session = start_interview(
        user_id, role, difficulty, language
    )

    st.session_state.current_question = next_question(
        st.session_state.session
    )

# =========================
# INTERVIEW FLOW
# =========================
if st.session_state.session:

    session = st.session_state.session

    # =========================
    # PROGRESS
    # =========================
    st.info(
        f"📊 Progress: Question {session.get('current_index', 0)} / {session.get('max_questions', 0)}"
    )

    st.subheader("Current Question")

    # =========================
    # QUESTION DISPLAY
    # =========================
    if session.get("completed"):
        st.success("🎉 Interview Completed!")

    elif st.session_state.current_question:
        st.info(st.session_state.current_question)

    user_answer = st.text_area("Your Answer")

    col1, col2 = st.columns(2)


    # =========================
    # SUBMIT ANSWER
    # =========================
    with col1:
        if st.button("Submit Answer"):

            if not user_answer.strip():
                st.warning("Please write an answer first.")
            else:
                evaluation = submit_answer(session, user_answer)

                st.success("Answer Submitted!")

                st.write("### Feedback")
                st.write(f"**Score:** {evaluation.get('score', 0)}/10")
                st.write(f"**Strengths:** {evaluation.get('strengths', '')}")
                st.write(f"**Weaknesses:** {evaluation.get('weaknesses', '')}")
                st.write(f"**Ideal Answer:** {evaluation.get('ideal_answer', '')}")

                if session.get("completed"):
                    st.success("🎉 Interview Completed!")


    # =========================
    # NEXT QUESTION
    # =========================
    with col2:
        if st.button("Next Question"):

            if not session.get("last_answered"):
                st.warning("Please submit your answer first!")
                st.stop()

            if session.get("completed"):
                st.warning("Interview already completed!")
                st.stop()

            new_q = next_question(session)

            if new_q is None:
                session["completed"] = True
                st.session_state.current_question = None
                st.success("🎉 Interview Completed!")
            else:
                st.session_state.current_question = new_q
                st.rerun()


# =========================
# RESULTS
# =========================
st.divider()
st.subheader("🎯 Interview Results")

if st.session_state.session:

    if st.session_state.session.get("completed"):

        results = get_results(st.session_state.session["interview_id"])

        st.success(f"⭐ Average Score: {results['average_score']:.2f}/10")

        st.write("### 📊 Detailed Feedback")

        for i, row in enumerate(results["details"], start=1):

            question, answer, score, strengths, weaknesses, ideal = row

            st.markdown(f"### Question {i}")
            st.write(f"**Q:** {question}")
            st.write(f"**Your Answer:** {answer}")
            st.write(f"**Score:** {score}/10")
            st.write(f"**Strengths:** {strengths}")
            st.write(f"**Weaknesses:** {weaknesses}")
            st.write(f"**Ideal Answer:** {ideal}")
            st.divider()

    else:
        st.info("Finish the interview to see results.")

else:
    st.info("Start an interview to see results.")


if is_admin:

    import pandas as pd
    import sqlite3
    import io

    if st.button("📥 Download Full Excel (Admin Only)"):

        conn = sqlite3.connect("interview.db")

        query = """
        SELECT 
            users.username,
            interviews.role,
            interviews.difficulty,
            interviews.language,
            questions.question_text,
            answers.answer_text,
            scores.score,
            interviews.created_at
        FROM interviews
        JOIN users ON users.id = interviews.user_id
        JOIN questions ON interviews.id = questions.interview_id
        JOIN answers ON questions.id = answers.question_id
        JOIN scores ON answers.id = scores.answer_id
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Interview Data")

        output.seek(0)

        st.download_button(
            label="⬇️ Download Excel",
            data=output,
            file_name="interview_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Admin access required to view export tools.")