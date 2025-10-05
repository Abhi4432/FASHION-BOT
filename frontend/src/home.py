import streamlit as st
import requests
from bot import show_bot_page
API_URL = "http://127.0.0.1:8000/login"

def show_login():
    st.title("👤 Fashion AI Login")

    username_or_email = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username_or_email and password:
            try:
                resp = requests.post(API_URL, json={
                    "username_or_email": username_or_email,
                    "password": password
                })
                if resp.status_code == 200:
                    data = resp.json()
                    if data["success"]:
                        st.session_state.logged_in = True
                        st.session_state.user_id = data["user_id"]
                        st.success("✅ Login successful!")
                        st.stop()
                    else:
                        st.error(data["msg"])
                else:
                    st.error("⚠️ Backend error")
            except requests.exceptions.RequestException:
                st.error("⚠️ Cannot reach backend")
        else:
            st.warning("Please enter username/email and password")
