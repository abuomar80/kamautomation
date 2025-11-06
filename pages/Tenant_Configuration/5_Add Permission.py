import streamlit as st
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

st.title("⛔ Add Permission")
st.markdown("---")

st.info("""
This page handles permission assignment.
Please implement the permission management functionality here.
""")

