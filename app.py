
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path
import streamlit as st
import os
import json


# =====================================================
# 1. INITIAL CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="TONY AI",
    page_icon="🤖",
    layout="wide"
)

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)

history_path = Path(__file__).resolve().parent / "history.json"

MODEL_NAME = "gemini-3.5-flash-lite"


# =====================================================
# 2. LOAD ALL USERS
# =====================================================

def load_users():

    if not history_path.exists():
        return {}

    try:
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError:
        st.error("history.json contains invalid JSON.")
        st.stop()


users = load_users()


# =====================================================
# 3. SAVE USERS
# =====================================================

def save_users():

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


# =====================================================
# 4. SAVE CURRENT USER'S CHAT HISTORY
# =====================================================

def save_history(chat_response, user_id):

    parsed = [
        msg.model_dump(mode="json", exclude_none=True)
        for msg in chat_response
    ]

    users[user_id]["history"] = parsed

    save_users()


# =====================================================
# 5. LOAD SPECIFIC USER'S CHAT HISTORY
# =====================================================

def load_history(user_id):

    if user_id not in users:
        return []

    return [
        types.Content.model_validate(msg)
        for msg in users[user_id]["history"]
    ]


# =====================================================
# 6. CREATE GEMINI CHAT
# =====================================================

def api_call(user_id):

    chat = client.chats.create(

        model=MODEL_NAME,

        history=load_history(user_id),

        config=types.GenerateContentConfig(

            system_instruction=(
                "You are a helpful chatbot." \
                "your role is to answer the question related to food testing, laboratory, science if somebody asks question that is not related to this type, politely say 'please ask questions related to laboratory 😊'"
                "Your name is TONY. "
                "Respond politely and clearly."
            )

        )
    )

    return chat


# =====================================================
# 7. EXTRACT TEXT FROM HISTORY
# =====================================================

def get_message_text(message):

    parts = message.get("parts", [])

    return "\n".join(
        part["text"]
        for part in parts
        if isinstance(part, dict) and part.get("text")
    )


# =====================================================
# 8. SESSION STATE INITIALIZATION
# =====================================================

if "active_user" not in st.session_state:
    st.session_state.active_user = None


# =====================================================
# 9. APPLICATION HEADER
# =====================================================

st.title("🤖 TONY AI")

st.caption("Your Personal AI Assistant")

st.divider()


# =====================================================
# 10. LOGIN / REGISTRATION PAGE
# =====================================================

if st.session_state.active_user is None:

    st.markdown("### Welcome to TONY!")

    st.write("Login or register using your EKA User ID.")

    with st.form("login_form"):

        user_id = st.text_input(
            "Enter your User ID",
            placeholder="Example: EKA001"
        )

        login_button = st.form_submit_button(
            "Login / Register",
            use_container_width=True
        )

    if login_button:

        user_id = user_id.strip().upper()

        if not user_id.startswith("EKA") or len(user_id) <= 3:

            st.error("Please enter a valid EKA User ID.")

        else:

            if user_id not in users:

                users[user_id] = {
                    "summary": "",
                    "history": []
                }

                save_users()

                st.success(
                    f"Account {user_id} created successfully!"
                )

            else:

                st.success(
                    f"Welcome back, {user_id}!"
                )

            st.session_state.active_user = user_id

            st.rerun()


# =====================================================
# 11. CHAT INTERFACE
# =====================================================

else:

    user_id = st.session_state.active_user

    # Sidebar
    with st.sidebar:

        st.title("🤖 TONY AI")

        st.divider()

        st.markdown("### User Profile")

        st.write(f"**User ID:** {user_id}")

        st.write(
            f"**Messages:** "
            f"{len(users[user_id]['history'])}"
        )

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True
        ):

            st.session_state.active_user = None

            st.rerun()

        st.caption("TONY AI Assistant")


    # Chat welcome message
    st.markdown(f"### Hello, {user_id}! 👋")

    st.write("How can I help you today?")

    # Display previous conversation
    for message in users[user_id]["history"]:

        role = message.get("role", "")

        if role == "user":
            with st.chat_message("user"):
                st.markdown(get_message_text(message))

        elif role == "model":
            with st.chat_message("assistant"):
                st.markdown(get_message_text(message))


    # Chat input
    query = st.chat_input("Ask TONY anything...")


    if query:

        # Display current user message
        with st.chat_message("user"):
            st.markdown(query)

        try:

            # Create Gemini chat with current user's history
            chat = api_call(user_id)

            # Send message to Gemini
            with st.chat_message("assistant"):

                with st.spinner("TONY is thinking..."):

                    response = chat.send_message(query)

                st.markdown(response.text)

            # Save complete conversation
            save_history(
                chat.get_history(),
                user_id
            )

            st.toast("Conversation saved successfully!")

        except Exception as e:

            st.error(f"An error occurred: {e}")


# =====================================================
# END OF APPLICATION
# =====================================================
