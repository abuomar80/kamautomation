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
    
    # Custom navigation system for Streamlit 1.28.2
    # Streamlit doesn't auto-detect pages in subdirectories, so we create custom navigation
    import os
    import sys
    import importlib.util
    
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
    selected_page_path = None
    
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
    
    # Debug: Show current page in sidebar
    if current_page:
        st.sidebar.caption(f"📄 {os.path.basename(current_page)}")
        # Verify file exists
        if not os.path.exists(current_page):
            st.sidebar.error("⚠️ File not found!")
            st.session_state['current_page'] = None
    
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
        # Load and display the selected page
        if os.path.exists(current_page):
            try:
                # Add root directory to path for imports
                root_dir = os.path.dirname(os.path.abspath(__file__))
                if root_dir not in sys.path:
                    sys.path.insert(0, root_dir)
                
                # Get the directory of the page file for relative imports
                page_dir = os.path.dirname(os.path.abspath(current_page))
                if page_dir not in sys.path:
                    sys.path.insert(0, page_dir)
                
                # Prepare comprehensive namespace with all necessary imports
                page_namespace = {
                    '__name__': '__main__',
                    '__file__': current_page,
                    '__package__': None,
                    'st': st,
                    'sys': sys,
                    'os': os,
                }
                
                # Add common imports that pages might need
                try:
                    import pandas as pd
                    page_namespace['pd'] = pd
                    page_namespace['pandas'] = pd
                except:
                    pass
                
                try:
                    import requests
                    page_namespace['requests'] = requests
                except:
                    pass
                
                try:
                    import yaml
                    page_namespace['yaml'] = yaml
                    from yaml import SafeLoader
                    page_namespace['SafeLoader'] = SafeLoader
                except:
                    pass
                
                try:
                    from legacy_session_state import legacy_session_state
                    page_namespace['legacy_session_state'] = legacy_session_state
                except ImportError as e:
                    # If legacy_session_state fails, continue without it
                    pass
                
                # Read the page file
                with open(current_page, 'r', encoding='utf-8') as f:
                    page_code = f.read()
                
                # Execute the page code in the prepared namespace
                # This will execute all Streamlit commands in the page file
                exec(page_code, page_namespace)
                
            except FileNotFoundError:
                st.error(f"Page file not found: {current_page}")
                st.info("Please check that the page file exists in the repository.")
            except SyntaxError as e:
                st.error(f"Syntax error in page file: {str(e)}")
                st.code(page_code if 'page_code' in locals() else '', language='python')
            except ImportError as e:
                st.error(f"Import error in page: {str(e)}")
                st.info("Make sure all required modules are in requirements.txt")
                st.exception(e)
            except Exception as e:
                st.error(f"Error loading page: {str(e)}")
                st.exception(e)
                # Show debug info
                with st.expander("Debug Information"):
                    st.write(f"Page path: {current_page}")
                    st.write(f"Page exists: {os.path.exists(current_page)}")
                    st.write(f"Root dir: {root_dir}")
                    st.write(f"Python path: {sys.path[:3]}")
        else:
            st.error(f"Page not found: {current_page}")
            st.info(f"Expected path: {os.path.abspath(current_page)}")
            # Reset to show welcome message
            if 'current_page' in st.session_state:
                del st.session_state['current_page']
            st.rerun()
    
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
