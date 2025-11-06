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
    
    # Navigation for Streamlit 1.28.2 (st.navigation not available in this version)
    # Use sidebar navigation with page links
    # Note: Streamlit 1.28.2 auto-detects pages in pages/ folder, but we create manual navigation
    
    st.sidebar.title("📋 Navigation")
    st.sidebar.markdown("---")
    
    # Define page groups with display names and file paths
    page_groups = {
        "📁 Tenant Configuration": [
            ("Tenant", "pages/Tenant_Configuration/0_Tenant.py"),
            ("Basic Configuration", "pages/Tenant_Configuration/1_Basic Configuration.py"),
            ("Advanced Configuration", "pages/Tenant_Configuration/2_Advanced Configuration.py"),
            ("SIP2 Configuration", "pages/Tenant_Configuration/3_SIP2 Configuration.py"),
            ("Default Users", "pages/Tenant_Configuration/4_Default Users.py"),
            ("Add Permission", "pages/Tenant_Configuration/5_Add Permission.py"),
            ("Z39.50", "pages/Tenant_Configuration/6_Z39.50.py"),
        ],
        "📦 Data Migration": [
            ("Users Import", "pages/Data_Migration/1_Users Import.py"),
            ("Circulation Loans", "pages/Data_Migration/2_Circulation Loans.py"),
            ("Fines", "pages/Data_Migration/3_Fines.py"),
            ("Marc Splitter", "pages/Data_Migration/4_Marc Splitter.py"),
        ],
        "⚙️ Other Configuration": [
            ("Clone Tenant", "pages/Other_Configuration/1_Clone Tenant.py"),
            ("Backup Tenant", "pages/Other_Configuration/2_Backup Tenant.py"),
        ],
    }
    
    # Display navigation menu
    for group_name, pages in page_groups.items():
        st.sidebar.markdown(f"### {group_name}")
        for page_name, page_path in pages:
            if st.sidebar.button(page_name, key=f"nav_{group_name}_{page_name}"):
                st.session_state['selected_page'] = page_path
                st.rerun()
        st.sidebar.markdown("---")
    
    # Load and execute selected page
    selected_page = st.session_state.get('selected_page', "pages/Tenant_Configuration/0_Tenant.py")
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("page_module", selected_page)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Add streamlit to module globals
            import sys
            module.__dict__['st'] = st
            spec.loader.exec_module(module)
    except Exception as e:
        st.error(f"Error loading page {selected_page}: {str(e)}")
        st.info("Please select a page from the sidebar navigation.")
    
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
