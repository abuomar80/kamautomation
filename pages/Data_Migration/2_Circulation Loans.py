import streamlit as st
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

st.set_page_config(page_title="Circulation Loans", layout="wide")

st.title("📙 Circulation Loans")
st.markdown("---")

st.info("""
This page handles loan transaction import.
Please implement the circulation loans functionality here.
""")

