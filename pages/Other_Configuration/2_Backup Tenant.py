import streamlit as st
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

st.set_page_config(page_title="Backup Tenant", layout="wide")

st.title("⚙️ Backup Tenant")
st.markdown("---")

st.info("""
This page handles tenant backup operations.
Please implement the backup tenant functionality here.
""")

