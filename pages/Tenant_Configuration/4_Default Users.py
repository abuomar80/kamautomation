import streamlit as st
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

st.title("👥 Default Users")
st.markdown("---")

st.info("""
This page handles default user creation.
Please implement the default users functionality here.
""")

