import streamlit as st
import requests
import re

API_URL = "http://127.0.0.1:8000/chat"

def show_bot_page():
    st.title("🤖 Fashion AI Bot")

    # ✅ Initialize session variables safely (UPDATED)
    for key, default in {
        "messages": [],
        "user_id": None,
        "logged_in": False,
        "user_input": "",
        "relevant_data": {} # FIX 1: Initialize relevant_data state
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # Reset/Logout buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Reset Conversation"):
            st.session_state.messages = []
            st.session_state.relevant_data = {} # FIX 2: Reset relevant_data on conversation reset
            st.success("Conversation reset.")
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.messages = []
            st.session_state.relevant_data = {} # Ensure full reset
            st.rerun()  # ✅ use st.rerun (new API)

    # Chat input
    user_input = st.text_input("💬 You:", key="chat_input", value="", placeholder="Ask about your orders or products...")
    if st.button("Send") and user_input.strip():
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        try:
            payload = {
                "messages": st.session_state.messages,
                "user_id": st.session_state.user_id,
                "relevant_data": st.session_state.relevant_data # FIX 3: Send current relevant_data
            }
            resp = requests.post(API_URL, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.messages = [dict(m) for m in data["messages"]]
                st.session_state.relevant_data = data["relevant_data"] # FIX 4: Store updated relevant_data
            else:
                st.error("⚠️ Backend error.")
        except requests.exceptions.RequestException:
            st.error("⚠️ Cannot reach backend.")

        # ✅ Use st.rerun() instead of trying to modify st.session_state.user_input
        st.rerun()

    # Display conversation history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"🧑 **You:** {msg['content']}")
        elif msg["role"] == "viewer_agent" and "http" in msg["content"]:
            # ✅ Render image if URL found in message
            img_urls = re.findall(r"http[s]?://\S+\.(?:jpg|jpeg|png)", msg["content"])
            st.markdown(f"🤖 **Bot:** {msg['content']}")
            for url in img_urls:
                st.image(url, caption="Product Image", width=250)
        else:
            st.markdown(f"🤖 **Bot:** {msg['content']}")








