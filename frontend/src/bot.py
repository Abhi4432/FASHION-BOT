import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/chat"

def show_bot_page():
    st.title("🤖 Fashion AI Bot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Reset Conversation"):
            st.session_state.messages = []
            st.success("Conversation reset.")
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.messages = []
            st.warning("🔒 Logged out.")
            st.stop()  # 🚨 force rerun to go back to login

    user_input = st.text_input("You:", key="user_input")
    if st.button("Send") and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        try:
            payload = {
                "messages": st.session_state.messages,
                "user_id": st.session_state.user_id
            }
            resp = requests.post(API_URL, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.messages = [dict(m) for m in data["messages"]]
            else:
                st.error("Backend error")
        except requests.exceptions.RequestException:
            st.error("Cannot reach backend")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Bot:** {msg['content']}")





