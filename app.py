import streamlit as st
import time
from gtts import gTTS
import speech_recognition as sr
from datetime import datetime
import os
import json
import base64
import google.generativeai as genai
from io import BytesIO

# ===================== CONFIG =====================
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=GEMINI_API_KEY)
TASKS_FILE = "tasks.json"

# ===================== SESSION STATE =====================
for key, default in {
    "timer_seconds": 25*60,
    "running": False,
    "custom_minutes": 25,
    "background": None,
    "tasks": [],
    "show_tutorial": True,
    "quote": "",
    "voice_text": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ===================== TASKS =====================
def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []

def save_tasks():
    with open(TASKS_FILE, "w") as f:
        json.dump(st.session_state.tasks, f)

st.session_state.tasks = load_tasks()

# ===================== TIMER =====================
def format_time(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{mins:02}:{secs:02}"

def update_timer():
    if st.session_state.running and st.session_state.timer_seconds > 0:
        st.session_state.timer_seconds -= 1
        time.sleep(1)
        st.experimental_rerun()

def start_timer(): st.session_state.running = True; st.experimental_rerun()
def stop_timer(): st.session_state.running = False
def reset_timer(): st.session_state.timer_seconds = st.session_state.custom_minutes*60; st.session_state.running=False

# ===================== TTS =====================
def speak(text):
    tts = gTTS(text=text, lang='en')
    tts_fp = BytesIO()
    tts.write_to_fp(tts_fp)
    tts_fp.seek(0)
    st.audio(tts_fp.read(), format="audio/mp3")

# ===================== GEMINI AI =====================
def get_gemini_quote():
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content("Generate a motivational quote related to productivity and success.")
        return response.text
    except Exception as e: return f"Error: {e}"

def ask_gemini(question):
    if not question: return "Please enter a question."
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(question)
        return response.text
    except Exception as e: return f"Error: {e}"

def ai_assist(task):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Help me complete this task: {task}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Error: {e}"

# ===================== VOICE ASSISTANT =====================
def record_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Recording... Speak now!")
        try:
            audio = recognizer.listen(source, timeout=10)
            st.session_state.voice_text = recognizer.recognize_google(audio)
            st.success(f"Recorded Text: {st.session_state.voice_text}")
        except sr.UnknownValueError:
            st.warning("Sorry, I could not understand the audio.")
        except sr.RequestError:
            st.warning("API request failed.")

def ask_gemini_about_voice():
    if st.session_state.voice_text.strip() == "":
        st.warning("No recorded text to ask Gemini.")
        return
    answer = ask_gemini(st.session_state.voice_text)
    st.markdown(
        f"""
        <div style='
            background-color: #1e3a5f;
            color: white;
            padding: 1rem;
            border-radius: 10px;
        '>{answer}</div>
        """,
        unsafe_allow_html=True
    )
    speak(answer)

# ===================== BACKGROUND =====================
if st.session_state.background:
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{st.session_state.background}");
        background-size: cover;
    }}
    </style>""", unsafe_allow_html=True)

# ===================== TUTORIAL =====================
if st.session_state.show_tutorial:
    st.title("🎓 Smart Desk Assistant Tutorial")
    st.markdown("""
        - ⏳ Use the Pomodoro timer to focus.
        - 🧠 Ask questions using Gemini AI.
        - 📝 Add tasks and get AI help.
        - 🎙 Text-to-speech or voice assistant.
        - 🌄 Upload a background to customize.
    """)
    if st.button("Got it! Start using the app", key="tutorial_button"):
        st.session_state.show_tutorial = False
        st.experimental_rerun()
    st.stop()

# ===================== APP UI =====================
st.title("🖥️ Smart Desk Assistant")
st.subheader("⏰ Current Time")
st.write(datetime.now().strftime("%H:%M:%S"))

# ===== Pomodoro Timer =====
st.subheader("⏳ Pomodoro Timer")
st.write(f"Time Left: **{format_time(st.session_state.timer_seconds)}**")
col1, col2, col3 = st.columns(3)
with col1: st.button("▶️ Start", on_click=start_timer, disabled=st.session_state.running, key="timer_start")
with col2: st.button("⏹ Stop", on_click=stop_timer, disabled=not st.session_state.running, key="timer_stop")
with col3: st.button("🔄 Reset", on_click=reset_timer, key="timer_reset")

st.subheader("⚙️ Timer Settings")
st.session_state.custom_minutes = st.slider("Set Timer (minutes)", 1, 60, 25, key="timer_slider")
st.button("Save Timer Duration", on_click=reset_timer, key="timer_save")

# ===== AI Quote =====
st.subheader("💡 AI-Generated Quote")
cols_q = st.columns([0.8, 0.2])
with cols_q[0]:
    if not st.session_state.quote:
        st.session_state.quote = get_gemini_quote()
    st.markdown(f"<div style='background-color: #1e3a5f; color:white; padding:1rem; border-radius:10px;'>{st.session_state.quote}</div>", unsafe_allow_html=True)
with cols_q[1]:
    if st.button("🔄 New Quote", key="quote_refresh"):
        st.session_state.quote = get_gemini_quote()
        st.experimental_rerun()

# ===== Text-to-Speech Input =====
st.subheader("🎙️ Text-to-Speech")
tts_input = st.text_area("Enter text for TTS:", height=80, key="tts_input")
st.button("🔊 Speak Text", on_click=lambda: speak(tts_input), key="tts_speak")

# ===== Voice Assistant =====
st.subheader("🎤 Voice Assistant")
col_rec, col_stop, col_ask = st.columns(3)
with col_rec: st.button("⏺ Record", on_click=record_voice, key="voice_record")
with col_stop: st.button("⏹ Stop", key="voice_stop")  # UI message only
with col_ask: st.button("💬 Ask Gemini about voice", on_click=ask_gemini_about_voice, key="voice_ask")
st.text_area("Last recorded text:", st.session_state.voice_text, height=60, key="voice_text_area")

# ===== Ask Gemini by Text =====
st.subheader("💬 Ask Gemini AI")
question = st.text_input("Enter your question:", key="question_input")
st.button("Ask Gemini", on_click=lambda: st.session_state.update({"gemini_answer": ask_gemini(question)}), key="ask_gemini_btn")
if "gemini_answer" in st.session_state:
    st.markdown(f"<div style='background-color:#1e3a5f; color:white; padding:1rem; border-radius:10px;'>{st.session_state.gemini_answer}</div>", unsafe_allow_html=True)

# ===== To-Do List =====
st.subheader("✅ To-Do List with AI Assistant")
new_task = st.text_input("Add new task:", key="new_task_input")
if st.button("Add Task", key="add_task_btn") and new_task:
    st.session_state.tasks.append({"task": new_task, "done": False})
    save_tasks()
    st.experimental_rerun()

for i, item in enumerate(st.session_state.tasks.copy()):
    cols = st.columns([0.05, 0.6, 0.2, 0.15])
    done = cols[0].checkbox("", value=item["done"], key=f"task_done_{i}")
    st.session_state.tasks[i]["done"] = done
    cols[1].markdown(f"✅ {item['task']}" if done else f"📝 {item['task']}")
    if cols[2].button("AI Help", key=f"ai_help_{i}"):
        response = ai_assist(item["task"])
        st.markdown(f"<div style='background-color:#0d2a3d; color:white; padding:1rem; border-radius:10px;'>{response}</div>", unsafe_allow_html=True)
    if cols[3].button("🗑️ Delete", key=f"delete_task_{i}"):
        st.session_state.tasks.pop(i)
        save_tasks()
        st.experimental_rerun()

# ===== Background Image =====
st.subheader("🖼️ Upload Background Image")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg","png"], key="bg_upload")
if uploaded_file:
    st.session_state.background = base64.b64encode(uploaded_file.read()).decode()
    st.experimental_rerun()

# ===== Timer Update =====
if st.session_state.running:
    update_timer()
