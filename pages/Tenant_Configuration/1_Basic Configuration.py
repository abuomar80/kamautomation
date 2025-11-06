import streamlit as st
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

st.title("⚙️ Basic Configuration")
st.markdown("---")

st.info("""
This page handles basic tenant configuration.
Please implement the basic configuration functionality here.
""")

