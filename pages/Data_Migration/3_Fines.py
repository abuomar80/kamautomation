import streamlit as st
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

st.set_page_config(page_title="Fines", layout="wide")

st.title("💵 Fines")
st.markdown("---")

st.info("""
This page handles fine policy management.
Please implement the fines functionality here.
""")

