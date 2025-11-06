import streamlit as st
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

st.set_page_config(page_title="Marc Splitter", layout="wide")

st.title("♻️ Marc Splitter")
st.markdown("---")

st.info("""
This page handles MARC file splitting.
Please implement the MARC splitter functionality here.
""")

