import streamlit as st
import time
from gtts import gTTS
import speech_recognition as sr
from datetime import datetime
import os
import json
import base64
import google.generativeai as genai

# Gemini API Key
GEMINI_API_KEY = "AIzaSyAvJhi8kIqaWFSX2Z3Dumd-hCQKwjnYTJc"
genai.configure(api_key=GEMINI_API_KEY)

# Persistent storage file
TASKS_FILE = "tasks.json"

# Session state initialization
if "timer_seconds" not in st.session_state:
    st.session_state.timer_seconds = 25 * 60
if "running" not in st.session_state:
    st.session_state.running = False
if "custom_minutes" not in st.session_state:
    st.session_state.custom_minutes = 25
if "background" not in st.session_state:
    st.session_state.background = None
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "show_tutorial" not in st.session_state:
    st.session_state.show_tutorial = True
if "quote" not in st.session_state:
    st.session_state.quote = ""

# Load saved tasks
def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# Save tasks to disk
def save_tasks():
    with open(TASKS_FILE, "w") as f:
        json.dump(st.session_state.tasks, f)

st.session_state.tasks = load_tasks()

# Format time
def format_time(seconds):
    mins, secs = divmod(seconds, 60)
    return f"{mins:02}:{secs:02}"

# Timer logic
def update_timer():
    if st.session_state.running and st.session_state.timer_seconds > 0:
        st.session_state.timer_seconds -= 1
        time.sleep(1)
        st.rerun()

def start_timer():
    st.session_state.running = True
    st.rerun()

def stop_timer():
    st.session_state.running = False

def reset_timer():
    st.session_state.timer_seconds = st.session_state.custom_minutes * 60
    st.session_state.running = False

# ✅ New TTS (Google TTS)
def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save("voice.mp3")
    st.audio("voice.mp3", autoplay=True)

# Voice Assistant
def voice_assistant():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening...")
        try:
            audio = recognizer.listen(source, timeout=15)
            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")
            speak(text)
        except sr.UnknownValueError:
            st.warning("Sorry, I couldn't understand.")
        except sr.RequestError:
            st.warning("API request error.")

# Gemini quote
def get_gemini_quote():
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content("Generate a motivational quote related to productivity and success.")
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Gemini Q&A
def ask_gemini(question):
    if not question:
        return "Please enter a question."
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(question)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# AI assist with tasks
def ai_assist(task):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Help me complete this task: {task}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Apply background
if st.session_state.background:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{st.session_state.background}");
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Tutorial on first load
if st.session_state.show_tutorial:
    st.title("🎓 Smart Desk Assistant Tutorial")
    st.markdown("""
        Welcome! Here's how to use the assistant:
        - ⏳ Use the Pomodoro timer to focus.
        - 🧠 Ask questions using Gemini AI.
        - 📝 Add tasks and let the assistant help or remind you.
        - 🎙 Use voice input.
        - 🌄 Upload a background to customize.
        """)
    if st.button("Got it! Start using the app"):
        st.session_state.show_tutorial = False
        st.rerun()
    st.stop()

# App title
st.title("🖥️ Smart Desk Assistant")

# Show current time
st.subheader("⏰ Current Time")
st.write(datetime.now().strftime("%H:%M:%S"))

# Timer UI
st.subheader("⏳ Pomodoro Timer")
st.write(f"Time Left: **{format_time(st.session_state.timer_seconds)}**")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶️ Start", disabled=st.session_state.running):
        start_timer()
with col2:
    if st.button("⏹ Stop", disabled=not st.session_state.running):
        stop_timer()
with col3:
    if st.button("🔄 Reset"):
        reset_timer()

# Timer settings
st.subheader("⚙️ Timer Settings")
st.session_state.custom_minutes = st.slider("Set Timer (minutes)", 1, 60, 25)
if st.button("Save Timer Duration"):
    reset_timer()

# AI Quote with refresh button
st.subheader("💡 AI-Generated Quote")
cols_q = st.columns([0.8, 0.2])
with cols_q[0]:
    if not st.session_state.quote:
        st.session_state.quote = get_gemini_quote()
    st.markdown(
        f"""
        <div style='
            background-color: #1e3a5f;
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            font-size: 16px;
            line-height: 1.6;
            max-width: 800px;
            margin: auto;
        '>{st.session_state.quote}</div>
        """,
        unsafe_allow_html=True
    )
with cols_q[1]:
    if st.button("🔄 New Quote"):
        st.session_state.quote = get_gemini_quote()
        st.rerun()

# Voice Assistant
st.subheader("🎙️ Voice Assistant")
if st.button("Speak"):
    voice_assistant()

# Ask Gemini
st.subheader("💬 Ask Gemini AI")
question = st.text_input("Enter your question:")
if st.button("Ask Gemini"):
    answer = ask_gemini(question)
    st.markdown(
        f"""
        <div style='
            background-color: #1e3a5f;
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            font-size: 16px;
            line-height: 1.6;
            max-width: 800px;
            margin: auto;
        '>{answer}</div>
        """,
        unsafe_allow_html=True
    )

# To-Do List
st.subheader("✅ To-Do List with AI Assistant")
new_task = st.text_input("Add new task:")
if st.button("Add Task") and new_task:
    st.session_state.tasks.append({"task": new_task, "done": False})
    save_tasks()
    st.rerun()

for i, item in enumerate(st.session_state.tasks.copy()):
    cols = st.columns([0.05, 0.6, 0.2, 0.15])
    done = cols[0].checkbox("", value=item["done"], key=f"task_done_{i}")
    st.session_state.tasks[i]["done"] = done
    cols[1].markdown(f"✅ {item['task']}" if done else f"📝 {item['task']}")
    
    if cols[2].button("AI Help", key=f"ai_help_{i}"):
        response = ai_assist(item["task"])
        st.markdown(
            f"""
            <div style='
                background-color: #0d2a3d;
                color: white;
                padding: 1.5rem;
                border-radius: 10px;
                font-size: 16px;
                line-height: 1.6;
                max-width: 800px;
                margin: auto;
            '>{response}</div>
            """,
            unsafe_allow_html=True
        )
    
    if cols[3].button("🗑️ Delete", key=f"delete_task_{i}"):
        st.session_state.tasks.pop(i)
        save_tasks()
        st.rerun()

# Background image
st.subheader("🖼️ Upload Background Image")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])
if uploaded_file is not None:
    image_data = uploaded_file.read()
    st.session_state.background = base64.b64encode(image_data).decode()
    st.rerun()

# Update timer
if st.session_state.running:
    update_timer()
