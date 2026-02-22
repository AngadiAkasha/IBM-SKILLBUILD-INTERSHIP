import streamlit as st
import PyPDF2
import pandas as pd
from datetime import datetime
import os
from utils.gemini_helper import get_gemini_response

# ------------------------------------------------
# Page config
# ------------------------------------------------
st.set_page_config(page_title="StudyMate AI", layout="wide")
RESULTS_FILE = "quiz_results.csv"
HISTORY_FILE = "history.json"

# ------------------------------------------------
# FILE STORAGE
# ------------------------------------------------
RESULTS_FILE = "quiz_results.csv"

if not os.path.exists(RESULTS_FILE):
    pd.DataFrame(columns=[
        "date", "score", "total", "accuracy", "confidence"
    ]).to_csv(RESULTS_FILE, index=False)

# ------------------------------------------------
# Custom CSS
# ------------------------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}
.hero {
    background: rgba(255,255,255,0.08);
    padding: 25px;
    border-radius: 18px;
    margin-bottom: 20px;
}
.chat-card {
    background: rgba(0,0,0,0.35);
    padding: 20px;
    border-radius: 18px;
    margin-bottom: 10px;
}
.user { color: #58a6ff; font-weight: 600; }
.ai { color: #7ee787; }
button, textarea { border-radius: 14px !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# Session State Defaults
# ------------------------------------------------
defaults = {
    "mode": "Explainer",
    "messages": [],
    "exam": "General",
    "difficulty": "Medium",
    "confidence": [],
    "quiz_questions": [],
    "current_q_index": 0,
    "quiz_active": False,
    "quiz_done": False,
    "user_answers": {},
    "score": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------------------------------------
# HERO
# ------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>🎓 StudyMate AI</h1>
    <p>AI-powered study assistant with exam-style MCQ assessment</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# TOP CONTROLS
# ------------------------------------------------
c1, c2, c3 = st.columns([2, 1, 1])
with c2:
    st.session_state.exam = st.selectbox(
        "🎯 Exam Mode", ["General", "Mid Exam", "Final Exam", "Viva"]
    )
with c3:
    st.session_state.difficulty = st.selectbox(
        "📊 Difficulty", ["Easy", "Medium", "Hard"]
    )

# ------------------------------------------------
# MODE SELECT
# ------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
with m1:
    if st.button("📘 Explainer", use_container_width=True):
        st.session_state.mode = "Explainer"
with m2:
    if st.button("📄 Summarizer", use_container_width=True):
        st.session_state.mode = "Summarizer"
with m3:
    if st.button("🧩 Quizzer", use_container_width=True):
        st.session_state.mode = "Quizzer"
with m4:
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.mode = "Dashboard"

st.markdown(f"### Current Mode: **{st.session_state.mode}**")

# =================================================
# 📘 EXPLAINER
# =================================================
if st.session_state.mode == "Explainer":

    for m in st.session_state.messages:
        st.markdown(
            f"<div class='chat-card'><span class='{m['role']}'>{m['content']}</span></div>",
            unsafe_allow_html=True
        )

    user_input = st.chat_input("Ask a concept…")
    if user_input:
        st.session_state.messages.append(
            {"role": "user", "content": "🧑‍🎓 " + user_input}
        )

        with st.spinner("🤖 Thinking…"):
            prompt = f"""
Reply like ChatGPT.

Rules:
- Short (5–7 bullet points max)
- Simple language
- No long paragraphs

Topic:
{user_input}
"""
            reply = get_gemini_response(prompt)

        st.session_state.messages.append(
            {"role": "ai", "content": reply}
        )
        st.rerun()

# =================================================
# 📄 SUMMARIZER
# =================================================
elif st.session_state.mode == "Summarizer":

    st.markdown("### 📄 Upload or Paste Study Material")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    text_input = st.text_area("Or paste notes", height=200)

    extracted_text = ""
    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            extracted_text += page.extract_text() or ""

    if text_input.strip():
        extracted_text += "\n" + text_input

    if st.button("✨ Summarize with AI"):
        if not extracted_text.strip():
            st.warning("⚠️ Please upload or paste content.")
        else:
            with st.spinner("🧠 Summarizing…"):
                prompt = f"""
Summarize briefly for exams.

Content:
{extracted_text[:12000]}
"""
                summary = get_gemini_response(prompt)

            st.markdown(
                f"<div class='chat-card ai'>{summary}</div>",
                unsafe_allow_html=True
            )

# =================================================
# 🧩 QUIZZER
# =================================================
elif st.session_state.mode == "Quizzer":

    st.markdown("### 🧩 MCQ Quiz Zone")

    topic = st.text_area("Enter topic for MCQs", height=120)
    num_questions = st.slider("Number of MCQs", 1, 1000, 5)

    if st.button("📝 Start MCQ Quiz"):
        if not topic.strip():
            st.warning("⚠️ Please enter a topic.")
        else:
            with st.spinner("🧠 Generating MCQs…"):
                prompt = f"""
Generate {num_questions} MCQs.

Rules:
- MCQs ONLY
- 4 options (A-D)
- One correct answer
- No explanations

Format:
Q1. Question
A. Option
B. Option
C. Option
D. Option
ANSWER: A

Topic:
{topic}
"""
                raw = get_gemini_response(prompt)

            blocks = raw.split("Q")
            questions = []

            for b in blocks:
                lines = [l.strip() for l in b.split("\n") if l.strip()]
                if len(lines) >= 6:
                    questions.append({
                        "question": lines[0][2:] if lines[0][0].isdigit() else lines[0],
                        "options": lines[1:5],
                        "answer": lines[5].replace("ANSWER:", "").strip()
                    })

            st.session_state.quiz_questions = questions
            st.session_state.current_q_index = 0
            st.session_state.quiz_active = True
            st.session_state.quiz_done = False
            st.session_state.user_answers = {}

    if st.session_state.quiz_active:
        idx = st.session_state.current_q_index
        qs = st.session_state.quiz_questions
        total = len(qs)

        if total > 0:
            st.progress(min((idx + 1) / total, 1.0))
            st.caption(f"Question {min(idx + 1, total)} of {total}")

        if idx < total:
            q = qs[idx]

            st.markdown(
                f"<div class='chat-card ai'><b>{q['question']}</b></div>",
                unsafe_allow_html=True
            )

            choice = st.radio("Choose an option", q["options"], key=f"mcq_{idx}")
            st.session_state.user_answers[idx] = choice

            if st.button("➡️ Next Question"):
                st.session_state.current_q_index += 1

        else:
            score = 0
            for i, q in enumerate(qs):
                if st.session_state.user_answers.get(i, "").startswith(q["answer"]):
                    score += 1

            st.session_state.score = score
            st.session_state.quiz_active = False
            st.session_state.quiz_done = True

    if st.session_state.quiz_done:

        total = len(st.session_state.quiz_questions)
        score = st.session_state.score
        percent = (score / total) * 100 if total else 0

        st.success("🎉 Quiz Completed!")
        st.markdown(f"### ✅ Score: {score} / {total}")
        st.markdown(f"### 📊 Accuracy: {percent:.2f}%")

        emoji = st.radio("How confident do you feel?", ["😕", "🙂", "😄", "🤩"], horizontal=True)

        if st.button("Save Result"):
            score_map = {"😕": 2, "🙂": 3, "😄": 4, "🤩": 5}
            conf = score_map[emoji]

            today = datetime.now().strftime("%Y-%m-%d")

            df = pd.read_csv(RESULTS_FILE)
            df = pd.concat([df, pd.DataFrame([{
                "date": today,
                "score": score,
                "total": total,
                "accuracy": percent,
                "confidence": conf
            }])], ignore_index=True)

            df.to_csv(RESULTS_FILE, index=False)
            st.success("💾 Result saved successfully!")

# =================================================
# 📊 DASHBOARD
# =================================================
elif st.session_state.mode == "Dashboard":

    st.markdown("## 📊 Learning Progress Dashboard")

    df = pd.read_csv(RESULTS_FILE)

    if df.empty:
        st.info("No quiz data yet. Take a quiz to see analytics.")
    else:
        df["date"] = pd.to_datetime(df["date"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Quizzes", len(df))
        c2.metric("Avg Accuracy", f"{df['accuracy'].mean():.1f}%")
        c3.metric("Avg Confidence", f"{df['confidence'].mean():.1f} / 5")

        st.divider()

        st.markdown("### 📈 Accuracy Over Time")
        st.line_chart(df.groupby("date")["accuracy"].mean())

        st.markdown("### 📊 Score Over Time")
        st.line_chart(df.groupby("date")["score"].mean())

        st.markdown("### 😊 Confidence Trend")
        st.line_chart(df.groupby("date")["confidence"].mean())

        with st.expander("📄 View Raw Data"):
            st.dataframe(df)
