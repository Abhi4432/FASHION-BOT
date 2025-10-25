import streamlit as st
import requests
import re

API_URL = "http://127.0.0.1:8000/chat"

def show_bot_page():
    st.title("🤖 Fashion AI Bot")

    # Initialize session variables safely
    for key, default in {
        "messages": [],
        "user_id": None,
        "logged_in": False,
        "relevant_data": {} 
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # Reset/Logout buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Reset Conversation"):
            st.session_state.messages = []
            st.session_state.relevant_data = {} 
            st.success("Conversation reset.")
            st.rerun() # Ensure full script rerun to clear chat area immediately
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.messages = []
            st.session_state.relevant_data = {}
            st.rerun()
    # ------------------------------------------------------------------
    # CHAT INPUT: Wrapped in a form to enable Enter key submission
    # ------------------------------------------------------------------
    with st.form(key='chat_form', clear_on_submit=True):
        user_input = st.text_input(
            "💬 You:", 
            key="chat_input", 
            value="", 
            placeholder="Ask about your orders, products, or recommendations...",
        )
        submitted = st.form_submit_button("Send", type="primary", use_container_width=True)


    if submitted and user_input.strip():
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        try:
            payload = {
                "messages": st.session_state.messages,
                "user_id": st.session_state.user_id,
                "relevant_data": st.session_state.relevant_data 
            }
            resp = requests.post(API_URL, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.messages = [dict(m) for m in data["messages"]]
                st.session_state.relevant_data = data["relevant_data"] 
            else:
                st.error("⚠️ Backend error.")
        except requests.exceptions.RequestException:
            st.error("⚠️ Cannot reach backend.")

        # Re-run the app to update the chat history display
        st.rerun()

    # ------------------------------------------------------------------
    # Display conversation history - FIXED IMAGE RENDERING
    # ------------------------------------------------------------------
    chat_history_container = st.container()

    # Regex to find a URL ending in an image extension
    IMG_URL_PATTERN = r"http[s]?://\S+\.(?:jpg|jpeg|png|gif)\b"

    with chat_history_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"🧑 **You:** {msg['content']}")
            
            elif msg["role"].endswith("_agent"):
                
                # --- NEW IMAGE LOGIC: Extract URL from message content ---
                image_urls = re.findall(IMG_URL_PATTERN, msg['content'])
                
                # Display the bot's text response first
                st.markdown(f"🤖 **Bot:** {msg['content']}")
                
                # Render any images found in this specific message
                for img_url in image_urls:
                    # Use the product name as the caption, if available
                    caption = st.session_state.relevant_data.get("name", "Product Image")
                    st.image(img_url, caption=caption, width=300)
                    # NOTE: No deletion needed here, as the URL is part of the message history.







