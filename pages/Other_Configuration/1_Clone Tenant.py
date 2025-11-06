import streamlit as st
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

st.set_page_config(page_title="Clone Tenant", layout="wide")

st.title("⚙️ Clone Tenant")
st.markdown("---")

st.info("""
This page handles tenant cloning operations.
Please implement the clone tenant functionality here.
""")

