import streamlit as st
from home import show_login
from bot import show_bot_page

st.set_page_config(page_title="Fashion AI", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.logged_in:
    show_login()
else:
    show_bot_page()


