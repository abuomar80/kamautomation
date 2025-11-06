import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml import SafeLoader
# Note: legacy_session_state is NOT called here to avoid conflicts with authenticator form
# Other pages that need it will call it themselves

st.set_page_config(
    page_title="KAM TEAM", layout="wide", initial_sidebar_state="expanded"
)

with open('authentication.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# Login form - stores authentication info in session_state
# In streamlit-authenticator 0.2.3, login() doesn't accept location parameter
# It renders the form in the main area by default
try:
    # Try calling login() without parameters (version 0.2.3)
    authenticator.login()
except TypeError as e:
    # If that fails, the method signature might be different
    # Try with form_name as positional argument (older API)
    try:
        authenticator.login('Login', 'main')
    except:
        # Last resort: try with just form_name
        authenticator.login('Login')

# Get authentication status from session_state (stored by authenticator)
name = st.session_state.get('name')
authentication_status = st.session_state.get('authentication_status')
username = st.session_state.get('username')

if authentication_status:
    # In streamlit-authenticator 0.2.3, logout() may not accept location parameter
    try:
        authenticator.logout(button_name='Logout', location='sidebar')
    except (TypeError, AttributeError):
        # Fallback: try without location parameter
        authenticator.logout(button_name='Logout')
    
    # Welcome message and main dashboard
    # Streamlit automatically detects pages in pages/ folder and creates navigation
    # This works the same way locally and on Streamlit Cloud
    st.title(f"Welcome, {name}! 👋")
    st.markdown("---")
    
    st.info("""
    **📋 Navigation:**
    
    Use the sidebar navigation (on the left) to access different pages.
    Streamlit automatically detects and lists all pages from the `pages/` folder.
    
    All pages are organized by category:
    - **📁 Tenant Configuration**: Tenant setup and configuration
    - **📦 Data Migration**: Import users, loans, fines, and MARC data  
    - **⚙️ Other Configuration**: Clone or backup tenant configurations
    """)
    
    st.markdown("### 🏠 Dashboard")
    st.markdown("""
    Select a page from the sidebar to get started with your FOLIO automation tasks.
    """)
    
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
