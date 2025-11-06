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
    
    # Use custom navigation that works reliably on both local and cloud
    # st.navigation may not work correctly on Streamlit Cloud even if available
    import os
    import sys
    
    # Define page structure
    page_mapping = {
        "📁 Tenant Configuration": {
            "Tenant": "pages/Tenant_Configuration/0_Tenant.py",
            "Basic Configuration": "pages/Tenant_Configuration/1_Basic Configuration.py",
            "Advanced Configuration": "pages/Tenant_Configuration/2_Advanced Configuration.py",
            "SIP2 Configuration": "pages/Tenant_Configuration/3_SIP2 Configuration.py",
            "Default Users": "pages/Tenant_Configuration/4_Default Users.py",
            "Add Permission": "pages/Tenant_Configuration/5_Add Permission.py",
            "Z39.50": "pages/Tenant_Configuration/6_Z39.50.py",
        },
        "📦 Data Migration": {
            "Users Import": "pages/Data_Migration/1_Users Import.py",
            "Circulation Loans": "pages/Data_Migration/2_Circulation Loans.py",
            "Fines": "pages/Data_Migration/3_Fines.py",
            "Marc Splitter": "pages/Data_Migration/4_Marc Splitter.py",
        },
        "⚙️ Other Configuration": {
            "Clone Tenant": "pages/Other_Configuration/1_Clone Tenant.py",
            "Backup Tenant": "pages/Other_Configuration/2_Backup Tenant.py",
        },
    }
    
    # Create sidebar navigation
    st.sidebar.markdown("## 📋 Navigation")
    st.sidebar.markdown("---")
    
    # Track which pages exist
    available_pages = {}
    
    for group_name, pages in page_mapping.items():
        st.sidebar.markdown(f"### {group_name}")
        group_available = {}
        for page_name, page_path in pages.items():
            # Check if page exists
            if os.path.exists(page_path):
                group_available[page_name] = page_path
                # Create navigation button
                button_key = f"nav_{group_name}_{page_name}"
                # Highlight current page button
                button_type = "primary" if st.session_state.get('current_page') == page_path else "secondary"
                if st.sidebar.button(page_name, key=button_key, use_container_width=True, type=button_type):
                    # Set the current page in session state
                    st.session_state['current_page'] = page_path
                    # Force rerun to load the page immediately
                    st.rerun()
        if group_available:
            available_pages[group_name] = group_available
        st.sidebar.markdown("---")
    
    # Get current page from session state
    current_page = st.session_state.get('current_page')
    
    # If no page selected, show welcome/dashboard
    if not current_page:
        st.title(f"Welcome, {name}! 👋")
        st.markdown("---")
        st.info("""
        **📋 Navigation:**
        
        Use the sidebar navigation (on the left) to access different pages.
        Click on any page name to load it.
        """)
        st.markdown("### 🏠 Dashboard")
        st.markdown("""
        Select a page from the sidebar to get started with your FOLIO automation tasks.
        """)
    else:
        # Load and display the selected page using importlib for proper module loading
        if os.path.exists(current_page):
            try:
                import importlib.util
                
                # Add root directory to path for imports
                root_dir = os.path.dirname(os.path.abspath(__file__))
                if root_dir not in sys.path:
                    sys.path.insert(0, root_dir)
                
                # Load page as a proper module
                spec = importlib.util.spec_from_file_location("page_module", current_page)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load spec for {current_page}")
                
                module = importlib.util.module_from_spec(spec)
                
                # Add necessary imports to module namespace
                module.__dict__['st'] = st
                module.__dict__['sys'] = sys
                module.__dict__['os'] = os
                
                # Add common imports
                try:
                    from legacy_session_state import legacy_session_state
                    module.__dict__['legacy_session_state'] = legacy_session_state
                except:
                    pass
                
                try:
                    import pandas as pd
                    module.__dict__['pd'] = pd
                except:
                    pass
                
                try:
                    import requests
                    module.__dict__['requests'] = requests
                except:
                    pass
                
                try:
                    import yaml
                    from yaml import SafeLoader
                    module.__dict__['yaml'] = yaml
                    module.__dict__['SafeLoader'] = SafeLoader
                except:
                    pass
                
                # Execute the module
                spec.loader.exec_module(module)
                
            except Exception as e:
                st.error(f"Error loading page: {str(e)}")
                st.exception(e)
                # Show debug info
                with st.expander("Debug Information"):
                    st.write(f"Page path: {current_page}")
                    st.write(f"Page exists: {os.path.exists(current_page)}")
                    st.write(f"Error type: {type(e).__name__}")
        else:
            st.error(f"Page not found: {current_page}")
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()
    
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
