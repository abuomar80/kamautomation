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
    
    # Dynamic page discovery and navigation
    import os
    import importlib.util
    
    # Define expected pages based on the created folder structure
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
    
    # Try alternative paths if pages/ folder doesn't exist
    def find_page_path(page_path):
        """Try to find the page file in different locations"""
        # Try original path
        if os.path.exists(page_path):
            return page_path
        # Try without pages/ prefix
        alt_path = page_path.replace("pages/", "")
        if os.path.exists(alt_path):
            return alt_path
        # Try with different naming
        base_name = os.path.basename(page_path)
        if os.path.exists(base_name):
            return base_name
        return None
    
    # Create sidebar navigation
    st.sidebar.title("📋 Navigation")
    st.sidebar.markdown("---")
    
    # Track available pages
    available_pages = {}
    
    for group_name, pages in page_mapping.items():
        st.sidebar.markdown(f"### {group_name}")
        group_pages = {}
        for page_name, page_path in pages.items():
            found_path = find_page_path(page_path)
            if found_path:
                group_pages[page_name] = found_path
                if st.sidebar.button(page_name, key=f"nav_{group_name}_{page_name}"):
                    st.session_state['selected_page'] = found_path
                    st.rerun()
        if group_pages:
            available_pages[group_name] = group_pages
        st.sidebar.markdown("---")
    
    # Load and display selected page
    selected_page = st.session_state.get('selected_page')
    
    # Show welcome message only if no page is selected
    if not selected_page:
        st.title(f"Welcome, {name}! 👋")
        st.markdown("---")
    
    if selected_page and os.path.exists(selected_page):
        try:
            # Prepare module namespace with all necessary imports
            import sys
            import importlib
            
            # Add current directory to Python path so pages can import root modules
            current_dir = os.path.dirname(os.path.abspath(selected_page))
            root_dir = os.path.dirname(os.path.abspath(__file__))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            # Create a comprehensive namespace for the page module
            page_namespace = {
                '__name__': '__main__',
                '__file__': selected_page,
                'st': st,
                'sys': sys,
                'os': os,
                'importlib': importlib,
            }
            
            # Add common imports that pages might need
            try:
                from legacy_session_state import legacy_session_state
                page_namespace['legacy_session_state'] = legacy_session_state
            except ImportError:
                pass
            
            # Try to import other common modules that pages might use
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
            except:
                pass
            
            # Read and execute the page file
            with open(selected_page, 'r', encoding='utf-8') as f:
                page_code = f.read()
            
            # Compile and execute the page code
            compiled_code = compile(page_code, selected_page, 'exec')
            exec(compiled_code, page_namespace)
            
        except FileNotFoundError:
            st.error(f"Page file not found: {selected_page}")
        except SyntaxError as e:
            st.error(f"Syntax error in page file: {str(e)}")
            st.code(page_code if 'page_code' in locals() else '', language='python')
        except Exception as e:
            st.error(f"Error loading page: {str(e)}")
            st.exception(e)
    else:
        # Show dashboard if no page selected or page not found
        if not available_pages:
            st.warning("""
            ⚠️ **No pages found!**
            
            Please ensure your page files are in the `pages/` directory or in the root directory.
            Expected structure:
            - `pages/Tenant_Configuration/0_Tenant.py`
            - `pages/Tenant_Configuration/1_Basic Configuration.py`
            - etc.
            """)
        else:
            # Default: show first available page or dashboard
            if not selected_page:
                # Set default page to first available
                first_group = list(available_pages.keys())[0] if available_pages else None
                if first_group:
                    first_page = list(available_pages[first_group].values())[0]
                    st.session_state['selected_page'] = first_page
                    st.rerun()
            else:
                st.info("""
                **📋 Dashboard**
                
                Select a page from the sidebar navigation to get started.
                Available pages are listed in the left sidebar.
                """)
    
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
