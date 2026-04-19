import streamlit as st
from backend import (
    start_interview,
    next_question,
    submit_answer,
    get_results
)

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
    st.session_state.session = start_interview(role, difficulty, language)

    st.session_state.current_question = next_question(st.session_state.session)


# =========================
# INTERVIEW FLOW
# =========================
if st.session_state.session:

    st.subheader("Current Question")

    if st.session_state.session.get("completed"):
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

            if user_answer.strip():

                evaluation = submit_answer(
                    st.session_state.session,
                    user_answer
                )

                st.success("Done!")

                st.write("### Feedback")
                st.write(f"**Score:** {evaluation['score']}/10")
                st.write(f"**Strengths:** {evaluation['strengths']}")
                st.write(f"**Weaknesses:** {evaluation['weaknesses']}")
                st.write(f"**Ideal Answer:** {evaluation['ideal_answer']}")

            else:
                st.warning("Please write an answer first.")


    # =========================
    # NEXT QUESTION
    # =========================
    with col2:
        if st.button("Next Question"):

            if st.session_state.session.get("completed"):
                st.warning("Interview already completed!")
                st.rerun()

            new_q = next_question(st.session_state.session)

            if new_q is None:
                st.session_state.current_question = None
                st.success("🎉 Interview Completed!")
            else:
                st.session_state.current_question = new_q
                st.rerun()


# =========================
# RESULTS
# =========================
st.divider()
st.subheader("Interview Results")

if st.session_state.session:

    results = get_results(st.session_state.session)

    st.write(f"**Average Score:** {results['average_score']:.2f}")

    for i, score in enumerate(results["scores"], start=1):
        st.write(f"Question {i}: {score}/10")

else:
    st.info("Start an interview to see results.")